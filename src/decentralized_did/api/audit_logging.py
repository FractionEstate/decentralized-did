"""
Enhanced Audit Logging for API Servers

Provides comprehensive audit logging capabilities:
- Structured JSON logging
- Request/response logging middleware
- Performance timing (request duration)
- PII sanitization (mask sensitive data)
- Correlation IDs (request tracking)
- Log rotation configuration
- Multiple log levels and handlers

License: Open-source (MIT)
"""

import logging
import logging.handlers
import json
import time
import uuid
import re
from typing import Optional, Dict, Any, List, Set, Callable
from datetime import datetime, timezone
from pathlib import Path
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import asyncio


# ============================================================================
# PII Sanitization
# ============================================================================

class PIISanitizer:
    """
    Sanitize PII (Personally Identifiable Information) from logs

    Masks:
    - Email addresses
    - Phone numbers
    - Credit card numbers
    - Social security numbers
    - IP addresses (optional)
    - API keys
    - JWT tokens
    - Biometric data (fingerprints, templates)
    """

    # Regex patterns for PII detection
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(
        r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
    CREDIT_CARD_PATTERN = re.compile(
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    IP_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    API_KEY_PATTERN = re.compile(
        r'\b(did_(?:prod|test)_[a-z0-9]{32})\b', re.IGNORECASE)
    JWT_PATTERN = re.compile(
        r'\bey[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b')
    HEX_HASH_PATTERN = re.compile(r'\b[a-fA-F0-9]{64,}\b')  # 256-bit+ hashes

    # Sensitive field names (for dict sanitization)
    SENSITIVE_FIELDS: Set[str] = {
        'password', 'secret', 'token', 'api_key', 'apikey', 'authorization',
        'biometric_data', 'fingerprint', 'template', 'helper_data',
        'private_key', 'signing_key', 'seed', 'mnemonic',
        'ssn', 'social_security', 'credit_card', 'cvv', 'pin',
    }

    def __init__(
        self,
        mask_emails: bool = True,
        mask_phones: bool = True,
        mask_credit_cards: bool = True,
        mask_ssn: bool = True,
        mask_ips: bool = False,  # Often needed for debugging
        mask_api_keys: bool = True,
        mask_jwt_tokens: bool = True,
        mask_biometric_data: bool = True,
        mask_char: str = '*',
        preserve_prefix_length: int = 4,
        preserve_suffix_length: int = 4,
    ):
        self.mask_emails = mask_emails
        self.mask_phones = mask_phones
        self.mask_credit_cards = mask_credit_cards
        self.mask_ssn = mask_ssn
        self.mask_ips = mask_ips
        self.mask_api_keys = mask_api_keys
        self.mask_jwt_tokens = mask_jwt_tokens
        self.mask_biometric_data = mask_biometric_data
        self.mask_char = mask_char
        self.preserve_prefix_length = preserve_prefix_length
        self.preserve_suffix_length = preserve_suffix_length

    def sanitize_string(self, text: str) -> str:
        """Sanitize a string by masking PII"""
        if not text:
            return text

        # Email addresses
        if self.mask_emails:
            text = self.EMAIL_PATTERN.sub(self._mask_email, text)

        # Phone numbers
        if self.mask_phones:
            text = self.PHONE_PATTERN.sub('[PHONE]', text)

        # Credit card numbers
        if self.mask_credit_cards:
            text = self.CREDIT_CARD_PATTERN.sub('[CARD]', text)

        # SSN
        if self.mask_ssn:
            text = self.SSN_PATTERN.sub('[SSN]', text)

        # IP addresses
        if self.mask_ips:
            text = self.IP_PATTERN.sub('[IP]', text)

        # API keys
        if self.mask_api_keys:
            text = self.API_KEY_PATTERN.sub(self._mask_api_key, text)

        # JWT tokens
        if self.mask_jwt_tokens:
            text = self.JWT_PATTERN.sub('[JWT]', text)

        # Biometric data (long hex hashes)
        if self.mask_biometric_data:
            text = self.HEX_HASH_PATTERN.sub(self._mask_hash, text)

        return text

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize a dictionary"""
        if not isinstance(data, dict):
            return data

        result = {}
        for key, value in data.items():
            # Check if key is sensitive
            key_lower = key.lower()
            is_sensitive = any(
                sensitive in key_lower
                for sensitive in self.SENSITIVE_FIELDS
            )

            if is_sensitive:
                # Mask the entire value
                if isinstance(value, str):
                    result[key] = self._mask_value(value)
                else:
                    result[key] = '[REDACTED]'
            elif isinstance(value, dict):
                # Recursively sanitize nested dicts
                result[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                # Sanitize list items
                result[key] = [
                    self.sanitize_dict(item) if isinstance(item, dict)
                    else self.sanitize_string(str(item)) if isinstance(item, str)
                    else item
                    for item in value
                ]
            elif isinstance(value, str):
                # Sanitize string values
                result[key] = self.sanitize_string(value)
            else:
                result[key] = value

        return result

    def _mask_email(self, match: re.Match) -> str:
        """Mask email address (keep first char + domain)"""
        email = match.group(0)
        parts = email.split('@')
        if len(parts) != 2:
            return '[EMAIL]'

        username = parts[0]
        domain = parts[1]

        if len(username) <= 2:
            masked_username = self.mask_char * len(username)
        else:
            masked_username = username[0] + \
                self.mask_char * (len(username) - 1)

        return f"{masked_username}@{domain}"

    def _mask_api_key(self, match: re.Match) -> str:
        """Mask API key (keep prefix and first few chars)"""
        api_key = match.group(0)
        if len(api_key) <= 20:
            return '[API_KEY]'

        # Keep "did_prod_" or "did_test_" prefix + first 4 chars
        prefix_end = api_key.index('_', 4) + 1  # After second underscore
        visible = api_key[:prefix_end + self.preserve_prefix_length]
        return visible + self.mask_char * (len(api_key) - len(visible))

    def _mask_hash(self, match: re.Match) -> str:
        """Mask long hex hash (keep first and last few chars)"""
        hash_str = match.group(0)
        if len(hash_str) <= 16:
            return hash_str  # Don't mask short hashes

        prefix = hash_str[:self.preserve_prefix_length]
        suffix = hash_str[-self.preserve_suffix_length:]
        middle = self.mask_char * 8
        return f"{prefix}{middle}{suffix}"

    def _mask_value(self, value: str) -> str:
        """Mask entire value (keep first and last few chars)"""
        if len(value) <= 8:
            return self.mask_char * len(value)

        prefix = value[:self.preserve_prefix_length]
        suffix = value[-self.preserve_suffix_length:]
        middle_len = len(value) - self.preserve_prefix_length - \
            self.preserve_suffix_length
        return f"{prefix}{self.mask_char * middle_len}{suffix}"


# ============================================================================
# Structured JSON Logging
# ============================================================================

class JSONFormatter(logging.Formatter):
    """
    Format log records as JSON

    Output format:
    {
        "timestamp": "2025-10-15T10:30:45.123Z",
        "level": "INFO",
        "logger": "api.server",
        "message": "Request processed",
        "context": {...}
    }
    """

    def __init__(
        self,
        sanitizer: Optional[PIISanitizer] = None,
        include_extra: bool = True,
    ):
        super().__init__()
        self.sanitizer = sanitizer or PIISanitizer()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        # Base log entry
        log_entry: Dict[str, Any] = {
            'timestamp': datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add extra context if present
        if self.include_extra and hasattr(record, 'context'):
            context = record.context
            if isinstance(context, dict):
                log_entry['context'] = self.sanitizer.sanitize_dict(context)
            else:
                log_entry['context'] = self.sanitizer.sanitize_string(
                    str(context))

        # Add other custom attributes
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'message', 'pathname', 'process', 'processName',
                'relativeCreated', 'thread', 'threadName', 'exc_info',
                'exc_text', 'stack_info', 'context'
            ]:
                if isinstance(value, dict):
                    log_entry[key] = self.sanitizer.sanitize_dict(value)
                elif isinstance(value, str):
                    log_entry[key] = self.sanitizer.sanitize_string(value)
                else:
                    log_entry[key] = value

        return json.dumps(log_entry)


# ============================================================================
# Audit Logger Configuration
# ============================================================================

class AuditLoggerConfig:
    """Configuration for audit logging"""

    def __init__(
        self,
        # Log file settings
        log_file: Optional[str] = None,
        log_dir: str = "logs",
        log_level: str = "INFO",

        # Rotation settings
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 10,

        # Formatting
        use_json_format: bool = True,
        sanitize_pii: bool = True,

        # Console logging
        console_output: bool = True,
        console_level: str = "INFO",

        # PII sanitization options
        mask_ips: bool = False,  # Often needed for debugging
        mask_biometric_data: bool = True,

        # Performance tracking
        track_performance: bool = True,
        slow_request_threshold: float = 1.0,  # seconds
    ):
        self.log_file = log_file
        self.log_dir = log_dir
        self.log_level = log_level

        self.max_bytes = max_bytes
        self.backup_count = backup_count

        self.use_json_format = use_json_format
        self.sanitize_pii = sanitize_pii

        self.console_output = console_output
        self.console_level = console_level

        self.mask_ips = mask_ips
        self.mask_biometric_data = mask_biometric_data

        self.track_performance = track_performance
        self.slow_request_threshold = slow_request_threshold

    @classmethod
    def production_config(cls) -> "AuditLoggerConfig":
        """Get production logging configuration"""
        return cls(
            log_file="audit.log",
            log_dir="logs",
            log_level="INFO",
            max_bytes=50 * 1024 * 1024,  # 50 MB
            backup_count=20,
            use_json_format=True,
            sanitize_pii=True,
            console_output=False,  # No console in production
            mask_ips=False,
            mask_biometric_data=True,
            track_performance=True,
            slow_request_threshold=1.0,
        )

    @classmethod
    def development_config(cls) -> "AuditLoggerConfig":
        """Get development logging configuration"""
        return cls(
            log_file="audit-dev.log",
            log_dir="logs",
            log_level="DEBUG",
            max_bytes=10 * 1024 * 1024,  # 10 MB
            backup_count=5,
            use_json_format=True,
            sanitize_pii=False,  # Don't sanitize in dev
            console_output=True,
            console_level="DEBUG",
            mask_ips=False,
            mask_biometric_data=False,
            track_performance=True,
            slow_request_threshold=0.5,
        )


# ============================================================================
# Audit Logger Setup
# ============================================================================

def setup_audit_logger(
    name: str = "api.audit",
    config: Optional[AuditLoggerConfig] = None
) -> logging.Logger:
    """
    Setup audit logger with structured JSON logging

    Args:
        name: Logger name
        config: Audit logger configuration

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_audit_logger(
        ...     name="api.server",
        ...     config=AuditLoggerConfig.production_config()
        ... )
        >>> logger.info("Server started", extra={'context': {'port': 8000}})
    """
    if config is None:
        config = AuditLoggerConfig.development_config()

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.log_level.upper()))
    logger.handlers = []  # Clear existing handlers

    # Create sanitizer if needed
    sanitizer = None
    if config.sanitize_pii:
        sanitizer = PIISanitizer(
            mask_ips=config.mask_ips,
            mask_biometric_data=config.mask_biometric_data,
        )

    # File handler (with rotation)
    if config.log_file:
        log_path = Path(config.log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_path / config.log_file,
            maxBytes=config.max_bytes,
            backupCount=config.backup_count,
        )

        if config.use_json_format:
            file_handler.setFormatter(JSONFormatter(sanitizer=sanitizer))
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )

        logger.addHandler(file_handler)

    # Console handler
    if config.console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(
            getattr(logging, config.console_level.upper()))

        if config.use_json_format:
            console_handler.setFormatter(JSONFormatter(sanitizer=sanitizer))
        else:
            console_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )

        logger.addHandler(console_handler)

    return logger


# ============================================================================
# Request/Response Logging Middleware
# ============================================================================

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses

    Logs:
    - Request ID (correlation)
    - Request method, path, headers
    - Response status, headers
    - Request duration (performance)
    - Slow request warnings
    """

    def __init__(
        self,
        app: ASGIApp,
        logger: Optional[logging.Logger] = None,
        config: Optional[AuditLoggerConfig] = None,
    ):
        super().__init__(app)
        self.config = config or AuditLoggerConfig.development_config()
        self.logger = logger or setup_audit_logger("api.audit", self.config)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response"""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Record start time
        start_time = time.time()

        # Log incoming request
        self._log_request(request, request_id)

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            duration = time.time() - start_time
            self._log_exception(request, request_id, e, duration)
            raise

        # Calculate duration
        duration = time.time() - start_time

        # Add request ID to response headers
        response.headers['X-Request-ID'] = request_id

        # Log response
        self._log_response(request, response, request_id, duration)

        return response

    def _log_request(self, request: Request, request_id: str) -> None:
        """Log incoming request"""
        context = {
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'query': str(request.url.query) if request.url.query else None,
            'client_ip': request.client.host if request.client else None,
            'user_agent': request.headers.get('user-agent'),
        }

        self.logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={'context': context}
        )

    def _log_response(
        self,
        request: Request,
        response: Response,
        request_id: str,
        duration: float
    ) -> None:
        """Log response"""
        context = {
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'duration_ms': round(duration * 1000, 2),
        }

        # Check for slow requests
        is_slow = duration > self.config.slow_request_threshold

        if is_slow:
            self.logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"({duration:.2f}s)",
                extra={'context': context}
            )
        else:
            self.logger.info(
                f"Response: {request.method} {request.url.path} "
                f"[{response.status_code}] ({duration:.3f}s)",
                extra={'context': context}
            )

    def _log_exception(
        self,
        request: Request,
        request_id: str,
        exception: Exception,
        duration: float
    ) -> None:
        """Log exception"""
        context = {
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'exception_type': type(exception).__name__,
            'duration_ms': round(duration * 1000, 2),
        }

        self.logger.error(
            f"Request failed: {request.method} {request.url.path} - "
            f"{type(exception).__name__}: {str(exception)}",
            extra={'context': context},
            exc_info=True
        )


# ============================================================================
# Convenience Functions
# ============================================================================

def setup_audit_logging(
    app,  # FastAPI app
    logger_name: str = "api.audit",
    config: Optional[AuditLoggerConfig] = None,
    environment: str = "production"
) -> logging.Logger:
    """
    Setup audit logging for FastAPI app

    Args:
        app: FastAPI application
        logger_name: Name for the logger
        config: Audit logger configuration (optional)
        environment: "production" or "development"

    Returns:
        Configured logger instance

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> logger = setup_audit_logging(app, environment="production")
    """
    if config is None:
        if environment == "production":
            config = AuditLoggerConfig.production_config()
        else:
            config = AuditLoggerConfig.development_config()

    logger = setup_audit_logger(logger_name, config)
    app.add_middleware(AuditLoggingMiddleware, logger=logger, config=config)

    logger.info(
        f"Audit logging configured for {environment}",
        extra={'context': {'environment': environment, 'logger': logger_name}}
    )

    return logger
