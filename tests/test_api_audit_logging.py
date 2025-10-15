"""
Tests for API Audit Logging

Tests audit logging functionality including:
- PII sanitization (emails, phones, API keys, biometric data)
- Structured JSON logging
- Request/response logging middleware
- Performance tracking
- Log rotation configuration

License: Open-source (MIT)
"""

from src.decentralized_did.api.audit_logging import (
    PIISanitizer,
    JSONFormatter,
    AuditLoggerConfig,
    AuditLoggingMiddleware,
    setup_audit_logger,
    setup_audit_logging,
)
import pytest
import json
import logging
import logging.handlers
import tempfile
import time
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request, Response

# Import audit logging module
import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


# ============================================================================
# Test PII Sanitization
# ============================================================================

class TestPIISanitizer:
    """Test PII sanitization"""

    def test_sanitize_email(self):
        """Test email address sanitization"""
        sanitizer = PIISanitizer(mask_emails=True)

        text = "Contact me at john.doe@example.com for details"
        result = sanitizer.sanitize_string(text)

        # Email should be masked (keeps first char + domain)
        assert "@example.com" in result
        assert "john.doe@example.com" not in result
        # Has masking    def test_sanitize_phone(self):
        assert result.count("*") > 0
        """Test phone number sanitization"""
        sanitizer = PIISanitizer(mask_phones=True)

        text = "Call me at 555-123-4567 or +1-555-987-6543"
        result = sanitizer.sanitize_string(text)

        assert "[PHONE]" in result
        assert "555-123-4567" not in result
        assert "+1-555-987-6543" not in result

    def test_sanitize_credit_card(self):
        """Test credit card sanitization"""
        sanitizer = PIISanitizer(mask_credit_cards=True)

        text = "Card: 4532-1234-5678-9010"
        result = sanitizer.sanitize_string(text)

        assert "[CARD]" in result
        assert "4532-1234-5678-9010" not in result

    def test_sanitize_ssn(self):
        """Test SSN sanitization"""
        sanitizer = PIISanitizer(mask_ssn=True)

        text = "SSN: 123-45-6789"
        result = sanitizer.sanitize_string(text)

        assert "[SSN]" in result
        assert "123-45-6789" not in result

    def test_sanitize_ip_address(self):
        """Test IP address sanitization"""
        sanitizer = PIISanitizer(mask_ips=True)

        text = "Request from 192.168.1.100"
        result = sanitizer.sanitize_string(text)

        assert "[IP]" in result
        assert "192.168.1.100" not in result

    def test_dont_sanitize_ip_by_default(self):
        """Test IP addresses not sanitized by default"""
        sanitizer = PIISanitizer(mask_ips=False)

        text = "Request from 192.168.1.100"
        result = sanitizer.sanitize_string(text)

        assert "192.168.1.100" in result

    def test_sanitize_api_key(self):
        """Test API key sanitization"""
        sanitizer = PIISanitizer(mask_api_keys=True)

        # Use a properly formatted API key (needs to match pattern)
        api_key = "did_prod_" + "a" * 32
        text = f"API key: {api_key}"
        result = sanitizer.sanitize_string(text)

        # Should keep prefix
        assert "did_prod_" in result
        # Full key should be masked or transformed
        assert result != text or api_key not in result

    def test_sanitize_jwt_token(self):
        """Test JWT token sanitization"""
        sanitizer = PIISanitizer(mask_jwt_tokens=True)

        text = "Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        result = sanitizer.sanitize_string(text)

        assert "[JWT]" in result
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result

    def test_sanitize_biometric_hash(self):
        """Test biometric hash sanitization"""
        sanitizer = PIISanitizer(mask_biometric_data=True)

        # 256-bit hash
        hash_256 = "a" * 64
        text = f"Biometric commitment: {hash_256}"
        result = sanitizer.sanitize_string(text)

        assert "aaaa" in result  # Prefix preserved
        assert "aaaa" in result[-8:]  # Suffix preserved
        assert "*" in result  # Middle masked
        assert hash_256 not in result

    def test_sanitize_dict_sensitive_fields(self):
        """Test dictionary sanitization for sensitive fields"""
        sanitizer = PIISanitizer()

        data = {
            "username": "john",
            "password": "secret123",
            "email": "john@example.com",
            "api_key": "did_prod_abc123xyz789",
            "biometric_data": "a" * 64,
        }

        result = sanitizer.sanitize_dict(data)

        assert result["username"] == "john"  # Not sensitive
        # Sensitive fields are masked (not necessarily "[REDACTED]")
        assert result["password"] != "secret123"
        assert "*" in result["password"] or result["password"] == "[REDACTED]"
        assert "@example.com" in result["email"]  # Domain kept
        assert "john@example.com" not in result["email"]  # Username masked
        assert result["api_key"] != "did_prod_abc123xyz789"
        assert result["biometric_data"] != "a" * 64

    def test_sanitize_nested_dict(self):
        """Test nested dictionary sanitization"""
        sanitizer = PIISanitizer()

        data = {
            "user": {
                "name": "John",
                "password": "secret",
                "contact": {
                    "email": "john@example.com",
                    "phone": "555-1234"
                }
            }
        }

        result = sanitizer.sanitize_dict(data)

        assert result["user"]["name"] == "John"
        # Password is masked (sensitive field)
        assert result["user"]["password"] != "secret"
        assert "@example.com" in result["user"]["contact"]["email"]

    def test_sanitize_list_in_dict(self):
        """Test list sanitization in dictionary"""
        sanitizer = PIISanitizer()

        data = {
            "users": [
                {"name": "John", "email": "john@example.com"},
                {"name": "Jane", "email": "jane@example.com"}
            ]
        }

        result = sanitizer.sanitize_dict(data)

        # Emails should be masked but domain preserved
        assert "@example.com" in result["users"][0]["email"]
        assert "john@example.com" not in result["users"][0]["email"]
        assert "@example.com" in result["users"][1]["email"]
        assert "jane@example.com" not in result["users"][1]["email"]

    def test_disable_all_sanitization(self):
        """Test disabling all sanitization"""
        sanitizer = PIISanitizer(
            mask_emails=False,
            mask_phones=False,
            mask_api_keys=False,
            mask_jwt_tokens=False,
            mask_biometric_data=False,
        )

        text = "Email: john@example.com, Phone: 555-1234, API: did_prod_abc123"
        result = sanitizer.sanitize_string(text)

        # Nothing should be masked
        assert "john@example.com" in result
        assert "555-1234" in result
        assert "did_prod_abc123" in result


# ============================================================================
# Test JSON Formatter
# ============================================================================

class TestJSONFormatter:
    """Test JSON log formatting"""

    def test_basic_formatting(self):
        """Test basic JSON log formatting"""
        formatter = JSONFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        log_entry = json.loads(result)

        assert log_entry["level"] == "INFO"
        assert log_entry["logger"] == "test.logger"
        assert log_entry["message"] == "Test message"
        assert "timestamp" in log_entry

    def test_format_with_context(self):
        """Test formatting with context"""
        sanitizer = PIISanitizer()
        formatter = JSONFormatter(sanitizer=sanitizer)

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="User action",
            args=(),
            exc_info=None,
        )
        record.context = {"user": "john", "email": "john@example.com"}

        result = formatter.format(record)
        log_entry = json.loads(result)

        assert "context" in log_entry
        assert log_entry["context"]["user"] == "john"
        # Email should be masked
        assert "@example.com" in log_entry["context"]["email"]
        assert "john@example.com" not in log_entry["context"]["email"]

    def test_format_with_exception(self):
        """Test formatting with exception"""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        log_entry = json.loads(result)

        assert "exception" in log_entry
        assert "ValueError: Test error" in log_entry["exception"]


# ============================================================================
# Test Audit Logger Config
# ============================================================================

class TestAuditLoggerConfig:
    """Test audit logger configuration"""

    def test_default_config(self):
        """Test default configuration"""
        config = AuditLoggerConfig()

        assert config.log_level == "INFO"
        assert config.use_json_format is True
        assert config.sanitize_pii is True
        assert config.console_output is True
        assert config.track_performance is True

    def test_production_config(self):
        """Test production configuration"""
        config = AuditLoggerConfig.production_config()

        assert config.log_file == "audit.log"
        assert config.log_level == "INFO"
        assert config.console_output is False  # No console in prod
        assert config.sanitize_pii is True
        assert config.max_bytes == 50 * 1024 * 1024  # 50 MB
        assert config.backup_count == 20

    def test_development_config(self):
        """Test development configuration"""
        config = AuditLoggerConfig.development_config()

        assert config.log_file == "audit-dev.log"
        assert config.log_level == "DEBUG"
        assert config.console_output is True
        assert config.sanitize_pii is False  # Don't sanitize in dev
        assert config.max_bytes == 10 * 1024 * 1024  # 10 MB
        assert config.backup_count == 5

    def test_custom_config(self):
        """Test custom configuration"""
        config = AuditLoggerConfig(
            log_file="custom.log",
            log_level="WARNING",
            max_bytes=1024,
            backup_count=3,
            console_output=False,
        )

        assert config.log_file == "custom.log"
        assert config.log_level == "WARNING"
        assert config.max_bytes == 1024
        assert config.backup_count == 3
        assert config.console_output is False


# ============================================================================
# Test Audit Logger Setup
# ============================================================================

class TestAuditLoggerSetup:
    """Test audit logger setup"""

    def test_setup_logger_with_file(self):
        """Test logger setup with file handler"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AuditLoggerConfig(
                log_file="test.log",
                log_dir=tmpdir,
                console_output=False,
            )

            logger = setup_audit_logger("test.logger", config)

            assert logger.level == logging.INFO
            assert len(logger.handlers) == 1
            assert isinstance(
                logger.handlers[0], logging.handlers.RotatingFileHandler)

    def test_setup_logger_with_console(self):
        """Test logger setup with console handler"""
        config = AuditLoggerConfig(
            log_file=None,
            console_output=True,
        )

        logger = setup_audit_logger("test.logger", config)

        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_setup_logger_with_both(self):
        """Test logger setup with file and console"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AuditLoggerConfig(
                log_file="test.log",
                log_dir=tmpdir,
                console_output=True,
            )

            logger = setup_audit_logger("test.logger", config)

            assert len(logger.handlers) == 2

    def test_logger_creates_directory(self):
        """Test logger creates log directory if missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "subdir" / "logs"

            config = AuditLoggerConfig(
                log_file="test.log",
                log_dir=str(log_dir),
                console_output=False,
            )

            logger = setup_audit_logger("test.logger", config)

            assert log_dir.exists()
            assert (log_dir / "test.log").exists()


# ============================================================================
# Test Audit Logging Middleware
# ============================================================================

class TestAuditLoggingMiddleware:
    """Test request/response logging middleware"""

    @pytest.mark.asyncio
    async def test_log_request_response(self):
        """Test logging request and response"""
        logger = logging.getLogger("test.middleware")
        logger.handlers = []  # Clear handlers

        # Add handler to capture logs
        handler = logging.handlers.MemoryHandler(capacity=100)
        logger.addHandler(handler)

        config = AuditLoggerConfig()
        middleware = AuditLoggingMiddleware(None, logger=logger, config=config)

        # Mock request
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/test"
        request.url.query = ""
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test-client"}
        request.state = Mock()

        # Mock response
        response = Response(content="OK", status_code=200)

        # Mock call_next
        async def mock_call_next(req):
            return response

        result = await middleware.dispatch(request, mock_call_next)

        assert result.status_code == 200
        assert "X-Request-ID" in result.headers

    @pytest.mark.asyncio
    async def test_log_slow_request(self):
        """Test logging slow requests"""
        logger = logging.getLogger("test.slow")
        logger.handlers = []

        handler = logging.handlers.MemoryHandler(capacity=100)
        logger.addHandler(handler)

        config = AuditLoggerConfig(slow_request_threshold=0.1)
        middleware = AuditLoggingMiddleware(None, logger=logger, config=config)

        # Mock request
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/slow"
        request.url.query = ""
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test-client"}
        request.state = Mock()

        # Mock slow response
        response = Response(content="OK", status_code=200)

        async def mock_slow_call_next(req):
            await asyncio.sleep(0.15)  # Slow request
            return response

        result = await middleware.dispatch(request, mock_slow_call_next)

        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_log_exception(self):
        """Test logging exceptions"""
        logger = logging.getLogger("test.exception")
        logger.handlers = []

        handler = logging.handlers.MemoryHandler(capacity=100)
        logger.addHandler(handler)

        config = AuditLoggerConfig()
        middleware = AuditLoggingMiddleware(None, logger=logger, config=config)

        # Mock request
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/api/error"
        request.url.query = ""
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test-client"}
        request.state = Mock()

        # Mock call_next that raises exception
        async def mock_error_call_next(req):
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await middleware.dispatch(request, mock_error_call_next)


# ============================================================================
# Test Integration
# ============================================================================

class TestAuditLoggingIntegration:
    """Test audit logging integration"""

    def test_end_to_end_logging(self):
        """Test end-to-end logging flow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AuditLoggerConfig(
                log_file="test-integration.log",
                log_dir=tmpdir,
                console_output=False,
                use_json_format=True,
                sanitize_pii=True,
            )

            logger = setup_audit_logger("test.integration", config)

            # Log various messages
            logger.info("Server started", extra={'context': {'port': 8000}})
            logger.warning("Slow request detected")
            logger.error("Authentication failed", extra={'context': {
                'user': 'john',
                'email': 'john@example.com',
                'api_key': 'did_prod_abc123'
            }})

            # Verify log file exists
            log_file = Path(tmpdir) / "test-integration.log"
            assert log_file.exists()

            # Read and verify log entries
            with open(log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3

                # Parse JSON
                log1 = json.loads(lines[0])
                assert log1["level"] == "INFO"
                assert log1["message"] == "Server started"

                log3 = json.loads(lines[2])
                assert log3["level"] == "ERROR"
                # Email should be sanitized (domain preserved)
                assert "@example.com" in str(log3["context"])
                assert "john@example.com" not in str(log3["context"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
