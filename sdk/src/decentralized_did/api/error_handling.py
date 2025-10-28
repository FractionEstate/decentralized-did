"""
Secure Error Handling for API Servers

Provides comprehensive error handling:
- Structured JSON error responses
- Production vs development error modes
- Request ID tracking in errors
- Error code taxonomy (categorized errors)
- Stack trace sanitization (production mode)
- Custom exception handlers
- HTTP status code mapping

License: Open-source (MIT)
"""

import logging
import traceback
import sys
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from datetime import datetime, timezone
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import json


# ============================================================================
# Error Code Taxonomy
# ============================================================================

class ErrorCategory(str, Enum):
    """Error categories for taxonomy"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    RATE_LIMIT = "rate_limit"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    SERVER_ERROR = "server_error"
    EXTERNAL_SERVICE = "external_service"
    BIOMETRIC = "biometric"
    BLOCKCHAIN = "blockchain"


class ErrorCode(str, Enum):
    """Standardized error codes"""
    # Authentication errors (AUTH_*)
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_MISSING_TOKEN = "AUTH_MISSING_TOKEN"
    AUTH_API_KEY_INVALID = "AUTH_API_KEY_INVALID"
    AUTH_API_KEY_REVOKED = "AUTH_API_KEY_REVOKED"

    # Authorization errors (AUTHZ_*)
    AUTHZ_INSUFFICIENT_PERMISSIONS = "AUTHZ_INSUFFICIENT_PERMISSIONS"
    AUTHZ_ROLE_REQUIRED = "AUTHZ_ROLE_REQUIRED"
    AUTHZ_RESOURCE_FORBIDDEN = "AUTHZ_RESOURCE_FORBIDDEN"

    # Validation errors (VAL_*)
    VAL_INVALID_INPUT = "VAL_INVALID_INPUT"
    VAL_MISSING_FIELD = "VAL_MISSING_FIELD"
    VAL_INVALID_FORMAT = "VAL_INVALID_FORMAT"
    VAL_INVALID_ADDRESS = "VAL_INVALID_ADDRESS"
    VAL_INVALID_DID = "VAL_INVALID_DID"
    VAL_INVALID_SIGNATURE = "VAL_INVALID_SIGNATURE"

    # Rate limiting errors (RATE_*)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    RATE_LIMIT_IP = "RATE_LIMIT_IP"
    RATE_LIMIT_WALLET = "RATE_LIMIT_WALLET"

    # Not found errors (NOT_FOUND_*)
    NOT_FOUND_RESOURCE = "NOT_FOUND_RESOURCE"
    NOT_FOUND_DID = "NOT_FOUND_DID"
    NOT_FOUND_TRANSACTION = "NOT_FOUND_TRANSACTION"

    # Conflict errors (CONFLICT_*)
    CONFLICT_DUPLICATE = "CONFLICT_DUPLICATE"
    CONFLICT_DID_EXISTS = "CONFLICT_DID_EXISTS"
    CONFLICT_STATE = "CONFLICT_STATE"

    # Server errors (SERVER_*)
    SERVER_INTERNAL_ERROR = "SERVER_INTERNAL_ERROR"
    SERVER_NOT_IMPLEMENTED = "SERVER_NOT_IMPLEMENTED"
    SERVER_MAINTENANCE = "SERVER_MAINTENANCE"

    # External service errors (EXT_*)
    EXT_KOIOS_ERROR = "EXT_KOIOS_ERROR"
    EXT_BLOCKCHAIN_ERROR = "EXT_BLOCKCHAIN_ERROR"
    EXT_SERVICE_UNAVAILABLE = "EXT_SERVICE_UNAVAILABLE"

    # Biometric errors (BIO_*)
    BIO_ENROLLMENT_FAILED = "BIO_ENROLLMENT_FAILED"
    BIO_VERIFICATION_FAILED = "BIO_VERIFICATION_FAILED"
    BIO_QUALITY_TOO_LOW = "BIO_QUALITY_TOO_LOW"
    BIO_TEMPLATE_INVALID = "BIO_TEMPLATE_INVALID"

    # Blockchain errors (BC_*)
    BC_TRANSACTION_FAILED = "BC_TRANSACTION_FAILED"
    BC_INSUFFICIENT_FUNDS = "BC_INSUFFICIENT_FUNDS"
    BC_INVALID_METADATA = "BC_INVALID_METADATA"


# Error code to category mapping
ERROR_CATEGORIES: Dict[ErrorCode, ErrorCategory] = {
    # Authentication
    ErrorCode.AUTH_INVALID_CREDENTIALS: ErrorCategory.AUTHENTICATION,
    ErrorCode.AUTH_TOKEN_EXPIRED: ErrorCategory.AUTHENTICATION,
    ErrorCode.AUTH_TOKEN_INVALID: ErrorCategory.AUTHENTICATION,
    ErrorCode.AUTH_MISSING_TOKEN: ErrorCategory.AUTHENTICATION,
    ErrorCode.AUTH_API_KEY_INVALID: ErrorCategory.AUTHENTICATION,
    ErrorCode.AUTH_API_KEY_REVOKED: ErrorCategory.AUTHENTICATION,

    # Authorization
    ErrorCode.AUTHZ_INSUFFICIENT_PERMISSIONS: ErrorCategory.AUTHORIZATION,
    ErrorCode.AUTHZ_ROLE_REQUIRED: ErrorCategory.AUTHORIZATION,
    ErrorCode.AUTHZ_RESOURCE_FORBIDDEN: ErrorCategory.AUTHORIZATION,

    # Validation
    ErrorCode.VAL_INVALID_INPUT: ErrorCategory.VALIDATION,
    ErrorCode.VAL_MISSING_FIELD: ErrorCategory.VALIDATION,
    ErrorCode.VAL_INVALID_FORMAT: ErrorCategory.VALIDATION,
    ErrorCode.VAL_INVALID_ADDRESS: ErrorCategory.VALIDATION,
    ErrorCode.VAL_INVALID_DID: ErrorCategory.VALIDATION,
    ErrorCode.VAL_INVALID_SIGNATURE: ErrorCategory.VALIDATION,

    # Rate limiting
    ErrorCode.RATE_LIMIT_EXCEEDED: ErrorCategory.RATE_LIMIT,
    ErrorCode.RATE_LIMIT_IP: ErrorCategory.RATE_LIMIT,
    ErrorCode.RATE_LIMIT_WALLET: ErrorCategory.RATE_LIMIT,

    # Not found
    ErrorCode.NOT_FOUND_RESOURCE: ErrorCategory.NOT_FOUND,
    ErrorCode.NOT_FOUND_DID: ErrorCategory.NOT_FOUND,
    ErrorCode.NOT_FOUND_TRANSACTION: ErrorCategory.NOT_FOUND,

    # Conflict
    ErrorCode.CONFLICT_DUPLICATE: ErrorCategory.CONFLICT,
    ErrorCode.CONFLICT_DID_EXISTS: ErrorCategory.CONFLICT,
    ErrorCode.CONFLICT_STATE: ErrorCategory.CONFLICT,

    # Server errors
    ErrorCode.SERVER_INTERNAL_ERROR: ErrorCategory.SERVER_ERROR,
    ErrorCode.SERVER_NOT_IMPLEMENTED: ErrorCategory.SERVER_ERROR,
    ErrorCode.SERVER_MAINTENANCE: ErrorCategory.SERVER_ERROR,

    # External services
    ErrorCode.EXT_KOIOS_ERROR: ErrorCategory.EXTERNAL_SERVICE,
    ErrorCode.EXT_BLOCKCHAIN_ERROR: ErrorCategory.EXTERNAL_SERVICE,
    ErrorCode.EXT_SERVICE_UNAVAILABLE: ErrorCategory.EXTERNAL_SERVICE,

    # Biometric
    ErrorCode.BIO_ENROLLMENT_FAILED: ErrorCategory.BIOMETRIC,
    ErrorCode.BIO_VERIFICATION_FAILED: ErrorCategory.BIOMETRIC,
    ErrorCode.BIO_QUALITY_TOO_LOW: ErrorCategory.BIOMETRIC,
    ErrorCode.BIO_TEMPLATE_INVALID: ErrorCategory.BIOMETRIC,

    # Blockchain
    ErrorCode.BC_TRANSACTION_FAILED: ErrorCategory.BLOCKCHAIN,
    ErrorCode.BC_INSUFFICIENT_FUNDS: ErrorCategory.BLOCKCHAIN,
    ErrorCode.BC_INVALID_METADATA: ErrorCategory.BLOCKCHAIN,
}


# Error code to HTTP status code mapping
ERROR_STATUS_CODES: Dict[ErrorCode, int] = {
    # Authentication - 401
    ErrorCode.AUTH_INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_TOKEN_EXPIRED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_TOKEN_INVALID: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_MISSING_TOKEN: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_API_KEY_INVALID: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_API_KEY_REVOKED: status.HTTP_401_UNAUTHORIZED,

    # Authorization - 403
    ErrorCode.AUTHZ_INSUFFICIENT_PERMISSIONS: status.HTTP_403_FORBIDDEN,
    ErrorCode.AUTHZ_ROLE_REQUIRED: status.HTTP_403_FORBIDDEN,
    ErrorCode.AUTHZ_RESOURCE_FORBIDDEN: status.HTTP_403_FORBIDDEN,

    # Validation - 400
    ErrorCode.VAL_INVALID_INPUT: status.HTTP_400_BAD_REQUEST,
    ErrorCode.VAL_MISSING_FIELD: status.HTTP_400_BAD_REQUEST,
    ErrorCode.VAL_INVALID_FORMAT: status.HTTP_400_BAD_REQUEST,
    ErrorCode.VAL_INVALID_ADDRESS: status.HTTP_400_BAD_REQUEST,
    ErrorCode.VAL_INVALID_DID: status.HTTP_400_BAD_REQUEST,
    ErrorCode.VAL_INVALID_SIGNATURE: status.HTTP_400_BAD_REQUEST,

    # Rate limiting - 429
    ErrorCode.RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.RATE_LIMIT_IP: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.RATE_LIMIT_WALLET: status.HTTP_429_TOO_MANY_REQUESTS,

    # Not found - 404
    ErrorCode.NOT_FOUND_RESOURCE: status.HTTP_404_NOT_FOUND,
    ErrorCode.NOT_FOUND_DID: status.HTTP_404_NOT_FOUND,
    ErrorCode.NOT_FOUND_TRANSACTION: status.HTTP_404_NOT_FOUND,

    # Conflict - 409
    ErrorCode.CONFLICT_DUPLICATE: status.HTTP_409_CONFLICT,
    ErrorCode.CONFLICT_DID_EXISTS: status.HTTP_409_CONFLICT,
    ErrorCode.CONFLICT_STATE: status.HTTP_409_CONFLICT,

    # Server errors - 500
    ErrorCode.SERVER_INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.SERVER_NOT_IMPLEMENTED: status.HTTP_501_NOT_IMPLEMENTED,
    ErrorCode.SERVER_MAINTENANCE: status.HTTP_503_SERVICE_UNAVAILABLE,

    # External services - 502/503
    ErrorCode.EXT_KOIOS_ERROR: status.HTTP_502_BAD_GATEWAY,
    ErrorCode.EXT_BLOCKCHAIN_ERROR: status.HTTP_502_BAD_GATEWAY,
    ErrorCode.EXT_SERVICE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,

    # Biometric - 400
    ErrorCode.BIO_ENROLLMENT_FAILED: status.HTTP_400_BAD_REQUEST,
    ErrorCode.BIO_VERIFICATION_FAILED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.BIO_QUALITY_TOO_LOW: status.HTTP_400_BAD_REQUEST,
    ErrorCode.BIO_TEMPLATE_INVALID: status.HTTP_400_BAD_REQUEST,

    # Blockchain - 400/500
    ErrorCode.BC_TRANSACTION_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.BC_INSUFFICIENT_FUNDS: status.HTTP_400_BAD_REQUEST,
    ErrorCode.BC_INVALID_METADATA: status.HTTP_400_BAD_REQUEST,
}


# ============================================================================
# Custom API Exception
# ============================================================================

class APIException(Exception):
    """
    Custom API exception with error code and details

    Example:
        >>> raise APIException(
        ...     error_code=ErrorCode.AUTH_TOKEN_EXPIRED,
        ...     message="Access token has expired",
        ...     details={"expired_at": "2025-10-15T10:00:00Z"}
        ... )
    """

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.status_code = status_code or ERROR_STATUS_CODES.get(
            error_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        self.category = ERROR_CATEGORIES.get(
            error_code, ErrorCategory.SERVER_ERROR)
        super().__init__(self.message)


# ============================================================================
# Error Response Formatter
# ============================================================================

class ErrorResponseFormatter:
    """
    Format error responses with consistent structure

    Production mode: Minimal error details (no stack traces)
    Development mode: Full error details (with stack traces)
    """

    def __init__(
        self,
        environment: str = "production",
        include_request_id: bool = True,
        include_timestamp: bool = True,
        include_stack_trace: Optional[bool] = None,
    ):
        self.environment = environment
        self.include_request_id = include_request_id
        self.include_timestamp = include_timestamp

        # Stack traces only in development by default
        if include_stack_trace is None:
            self.include_stack_trace = (environment == "development")
        else:
            self.include_stack_trace = include_stack_trace

    def format_error(
        self,
        error: Exception,
        request: Optional[Request] = None,
        status_code: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Format an exception into a structured error response

        Args:
            error: The exception to format
            request: FastAPI request object (for request ID)
            status_code: HTTP status code (optional)

        Returns:
            Structured error dictionary
        """
        # Base error response
        error_response: Dict[str, Any] = {
            "error": True,
        }

        # Add timestamp
        if self.include_timestamp:
            error_response["timestamp"] = datetime.now(
                timezone.utc).isoformat()

        # Add request ID if available
        if self.include_request_id and request:
            request_id = getattr(request.state, "request_id", None)
            if request_id:
                error_response["request_id"] = request_id

        # Handle APIException (our custom exceptions)
        if isinstance(error, APIException):
            error_response["code"] = error.error_code.value
            error_response["category"] = error.category.value
            error_response["message"] = error.message

            if error.details:
                error_response["details"] = error.details

            if status_code is None:
                status_code = error.status_code

        # Handle FastAPI validation errors
        elif isinstance(error, RequestValidationError):
            error_response["code"] = ErrorCode.VAL_INVALID_INPUT.value
            error_response["category"] = ErrorCategory.VALIDATION.value
            error_response["message"] = "Invalid request data"
            error_response["details"] = {
                "validation_errors": [
                    {
                        "loc": list(err["loc"]),
                        "msg": err["msg"],
                        "type": err["type"],
                    }
                    for err in error.errors()
                ]
            }

            if status_code is None:
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

        # Handle Starlette HTTP exceptions
        elif isinstance(error, StarletteHTTPException):
            error_response["code"] = self._status_to_error_code(
                error.status_code).value
            error_response["category"] = ERROR_CATEGORIES.get(
                self._status_to_error_code(error.status_code),
                ErrorCategory.SERVER_ERROR
            ).value
            error_response["message"] = error.detail

            if status_code is None:
                status_code = error.status_code

        # Handle generic exceptions
        else:
            error_response["code"] = ErrorCode.SERVER_INTERNAL_ERROR.value
            error_response["category"] = ErrorCategory.SERVER_ERROR.value

            if self.environment == "development":
                # Full error details in development
                error_response["message"] = str(error)
                error_response["type"] = type(error).__name__
            else:
                # Generic message in production
                error_response["message"] = "An internal server error occurred"

            if status_code is None:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        # Add stack trace if enabled (respects explicit override)
        if self.include_stack_trace:
            error_response["stack_trace"] = traceback.format_exc()

        error_response["status_code"] = status_code

        return error_response

    def _status_to_error_code(self, status_code: int) -> ErrorCode:
        """Map HTTP status code to error code"""
        if status_code == 401:
            return ErrorCode.AUTH_MISSING_TOKEN
        elif status_code == 403:
            return ErrorCode.AUTHZ_INSUFFICIENT_PERMISSIONS
        elif status_code == 404:
            return ErrorCode.NOT_FOUND_RESOURCE
        elif status_code == 409:
            return ErrorCode.CONFLICT_STATE
        elif status_code == 429:
            return ErrorCode.RATE_LIMIT_EXCEEDED
        elif status_code == 503:
            return ErrorCode.SERVER_MAINTENANCE
        else:
            return ErrorCode.SERVER_INTERNAL_ERROR


# ============================================================================
# Exception Handlers
# ============================================================================

def create_exception_handlers(
    formatter: Optional[ErrorResponseFormatter] = None,
    logger: Optional[logging.Logger] = None,
) -> Dict[Any, Callable]:
    """
    Create exception handlers for FastAPI

    Args:
        formatter: Error response formatter
        logger: Logger for error logging

    Returns:
        Dictionary of exception handlers

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> handlers = create_exception_handlers()
        >>> for exc_class, handler in handlers.items():
        ...     app.add_exception_handler(exc_class, handler)
    """
    if formatter is None:
        formatter = ErrorResponseFormatter(environment="production")

    if logger is None:
        logger = logging.getLogger("api.errors")

    async def handle_api_exception(request: Request, exc: APIException) -> JSONResponse:
        """Handle APIException"""
        error_response = formatter.format_error(exc, request, exc.status_code)

        # Log the error
        logger.error(
            f"API Error: {exc.error_code.value} - {exc.message}",
            extra={
                "context": {
                    "error_code": exc.error_code.value,
                    "category": exc.category.value,
                    "request_id": getattr(request.state, "request_id", None),
                    "path": request.url.path,
                }
            }
        )

        return JSONResponse(
            status_code=error_response["status_code"],
            content=error_response
        )

    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """Handle validation errors"""
        error_response = formatter.format_error(exc, request)

        logger.warning(
            f"Validation error: {len(exc.errors())} errors",
            extra={
                "context": {
                    "request_id": getattr(request.state, "request_id", None),
                    "path": request.url.path,
                    "errors": exc.errors(),
                }
            }
        )

        return JSONResponse(
            status_code=error_response["status_code"],
            content=error_response
        )

    async def handle_http_exception(
        request: Request,
        exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions"""
        error_response = formatter.format_error(exc, request, exc.status_code)

        logger.warning(
            f"HTTP error: {exc.status_code} - {exc.detail}",
            extra={
                "context": {
                    "request_id": getattr(request.state, "request_id", None),
                    "path": request.url.path,
                    "status_code": exc.status_code,
                }
            }
        )

        return JSONResponse(
            status_code=error_response["status_code"],
            content=error_response
        )

    async def handle_generic_exception(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Handle generic exceptions"""
        error_response = formatter.format_error(exc, request)

        logger.exception(
            f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
            extra={
                "context": {
                    "request_id": getattr(request.state, "request_id", None),
                    "path": request.url.path,
                }
            },
            exc_info=True
        )

        return JSONResponse(
            status_code=error_response["status_code"],
            content=error_response
        )

    return {
        APIException: handle_api_exception,
        RequestValidationError: handle_validation_error,
        StarletteHTTPException: handle_http_exception,
        Exception: handle_generic_exception,
    }


# ============================================================================
# Setup Function
# ============================================================================

def setup_error_handling(
    app,  # FastAPI app
    environment: str = "production",
    logger: Optional[logging.Logger] = None,
) -> ErrorResponseFormatter:
    """
    Setup error handling for FastAPI app

    Args:
        app: FastAPI application
        environment: "production" or "development"
        logger: Logger for error logging (optional)

    Returns:
        Error response formatter

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> formatter = setup_error_handling(app, environment="production")
    """
    formatter = ErrorResponseFormatter(environment=environment)
    handlers = create_exception_handlers(formatter=formatter, logger=logger)

    for exc_class, handler in handlers.items():
        app.add_exception_handler(exc_class, handler)

    if logger:
        logger.info(
            f"Error handling configured for {environment}",
            extra={"context": {"environment": environment}}
        )

    return formatter
