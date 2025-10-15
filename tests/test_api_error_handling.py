"""
Tests for API Error Handling

Tests error handling functionality including:
- Error code taxonomy
- Custom API exceptions
- Error response formatting (production/development)
- Request ID tracking
- Stack trace sanitization
- Exception handlers

License: Open-source (MIT)
"""

from src.decentralized_did.api.error_handling import (
    ErrorCategory,
    ErrorCode,
    ERROR_CATEGORIES,
    ERROR_STATUS_CODES,
    APIException,
    ErrorResponseFormatter,
    create_exception_handlers,
    setup_error_handling,
)
import pytest
import json
from unittest.mock import Mock, AsyncMock
from fastapi import Request, status as http_status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

# Import error handling module
import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


# ============================================================================
# Test Error Taxonomy
# ============================================================================

class TestErrorTaxonomy:
    """Test error code taxonomy"""

    def test_error_categories_exist(self):
        """Test all error categories are defined"""
        categories = [
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.AUTHORIZATION,
            ErrorCategory.VALIDATION,
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.NOT_FOUND,
            ErrorCategory.CONFLICT,
            ErrorCategory.SERVER_ERROR,
            ErrorCategory.EXTERNAL_SERVICE,
            ErrorCategory.BIOMETRIC,
            ErrorCategory.BLOCKCHAIN,
        ]

        assert len(categories) == 10

    def test_error_codes_exist(self):
        """Test error codes are defined"""
        # Sample error codes from each category
        codes = [
            ErrorCode.AUTH_TOKEN_EXPIRED,
            ErrorCode.AUTHZ_INSUFFICIENT_PERMISSIONS,
            ErrorCode.VAL_INVALID_INPUT,
            ErrorCode.RATE_LIMIT_EXCEEDED,
            ErrorCode.NOT_FOUND_RESOURCE,
            ErrorCode.CONFLICT_DUPLICATE,
            ErrorCode.SERVER_INTERNAL_ERROR,
            ErrorCode.EXT_SERVICE_UNAVAILABLE,
            ErrorCode.BIO_ENROLLMENT_FAILED,
            ErrorCode.BC_TRANSACTION_FAILED,
        ]

        assert len(codes) == 10

    def test_error_category_mapping(self):
        """Test error codes map to correct categories"""
        assert ERROR_CATEGORIES[ErrorCode.AUTH_TOKEN_EXPIRED] == ErrorCategory.AUTHENTICATION
        assert ERROR_CATEGORIES[ErrorCode.AUTHZ_INSUFFICIENT_PERMISSIONS] == ErrorCategory.AUTHORIZATION
        assert ERROR_CATEGORIES[ErrorCode.VAL_INVALID_INPUT] == ErrorCategory.VALIDATION
        assert ERROR_CATEGORIES[ErrorCode.RATE_LIMIT_EXCEEDED] == ErrorCategory.RATE_LIMIT
        assert ERROR_CATEGORIES[ErrorCode.NOT_FOUND_RESOURCE] == ErrorCategory.NOT_FOUND

    def test_error_status_code_mapping(self):
        """Test error codes map to correct HTTP status codes"""
        assert ERROR_STATUS_CODES[ErrorCode.AUTH_TOKEN_EXPIRED] == http_status.HTTP_401_UNAUTHORIZED
        assert ERROR_STATUS_CODES[ErrorCode.AUTHZ_INSUFFICIENT_PERMISSIONS] == http_status.HTTP_403_FORBIDDEN
        assert ERROR_STATUS_CODES[ErrorCode.VAL_INVALID_INPUT] == http_status.HTTP_400_BAD_REQUEST
        assert ERROR_STATUS_CODES[ErrorCode.RATE_LIMIT_EXCEEDED] == http_status.HTTP_429_TOO_MANY_REQUESTS
        assert ERROR_STATUS_CODES[ErrorCode.NOT_FOUND_RESOURCE] == http_status.HTTP_404_NOT_FOUND


# ============================================================================
# Test APIException
# ============================================================================

class TestAPIException:
    """Test custom API exception"""

    def test_create_api_exception(self):
        """Test creating API exception"""
        exc = APIException(
            error_code=ErrorCode.AUTH_TOKEN_EXPIRED,
            message="Token has expired"
        )

        assert exc.error_code == ErrorCode.AUTH_TOKEN_EXPIRED
        assert exc.message == "Token has expired"
        assert exc.details == {}
        assert exc.status_code == http_status.HTTP_401_UNAUTHORIZED
        assert exc.category == ErrorCategory.AUTHENTICATION

    def test_api_exception_with_details(self):
        """Test API exception with details"""
        exc = APIException(
            error_code=ErrorCode.VAL_INVALID_ADDRESS,
            message="Invalid Cardano address",
            details={"address": "addr1invalid", "reason": "Invalid format"}
        )

        assert exc.details["address"] == "addr1invalid"
        assert exc.details["reason"] == "Invalid format"

    def test_api_exception_custom_status(self):
        """Test API exception with custom status code"""
        exc = APIException(
            error_code=ErrorCode.SERVER_INTERNAL_ERROR,
            message="Custom error",
            status_code=418  # I'm a teapot
        )

        assert exc.status_code == 418

    def test_api_exception_str(self):
        """Test API exception string representation"""
        exc = APIException(
            error_code=ErrorCode.NOT_FOUND_DID,
            message="DID not found"
        )

        assert str(exc) == "DID not found"


# ============================================================================
# Test ErrorResponseFormatter
# ============================================================================

class TestErrorResponseFormatter:
    """Test error response formatting"""

    def test_production_formatter(self):
        """Test production mode formatter"""
        formatter = ErrorResponseFormatter(environment="production")

        assert formatter.environment == "production"
        assert formatter.include_stack_trace is False

    def test_development_formatter(self):
        """Test development mode formatter"""
        formatter = ErrorResponseFormatter(environment="development")

        assert formatter.environment == "development"
        assert formatter.include_stack_trace is True

    def test_format_api_exception(self):
        """Test formatting API exception"""
        formatter = ErrorResponseFormatter(environment="production")

        exc = APIException(
            error_code=ErrorCode.AUTH_TOKEN_EXPIRED,
            message="Token expired"
        )

        result = formatter.format_error(exc)

        assert result["error"] is True
        assert result["code"] == "AUTH_TOKEN_EXPIRED"
        assert result["category"] == "authentication"
        assert result["message"] == "Token expired"
        assert result["status_code"] == 401
        assert "timestamp" in result

    def test_format_api_exception_with_details(self):
        """Test formatting API exception with details"""
        formatter = ErrorResponseFormatter(environment="production")

        exc = APIException(
            error_code=ErrorCode.VAL_INVALID_INPUT,
            message="Invalid input",
            details={"field": "email", "issue": "Invalid format"}
        )

        result = formatter.format_error(exc)

        assert "details" in result
        assert result["details"]["field"] == "email"

    def test_format_api_exception_with_request_id(self):
        """Test formatting with request ID"""
        formatter = ErrorResponseFormatter(environment="production")

        # Mock request with request_id
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.request_id = "test-request-123"

        exc = APIException(
            error_code=ErrorCode.SERVER_INTERNAL_ERROR,
            message="Internal error"
        )

        result = formatter.format_error(exc, request=request)

        assert result["request_id"] == "test-request-123"

    def test_format_generic_exception_production(self):
        """Test formatting generic exception in production"""
        formatter = ErrorResponseFormatter(environment="production")

        exc = ValueError("Something went wrong")
        result = formatter.format_error(exc)

        assert result["code"] == "SERVER_INTERNAL_ERROR"
        assert result["category"] == "server_error"
        assert result["message"] == "An internal server error occurred"
        assert "stack_trace" not in result  # No stack trace in production

    def test_format_generic_exception_development(self):
        """Test formatting generic exception in development"""
        formatter = ErrorResponseFormatter(environment="development")

        exc = ValueError("Something went wrong")
        result = formatter.format_error(exc)

        assert result["message"] == "Something went wrong"
        assert result["type"] == "ValueError"
        assert "stack_trace" in result  # Stack trace in development

    def test_format_http_exception(self):
        """Test formatting HTTP exception"""
        formatter = ErrorResponseFormatter(environment="production")

        exc = StarletteHTTPException(status_code=404, detail="Not found")
        result = formatter.format_error(exc)

        assert result["code"] == "NOT_FOUND_RESOURCE"
        assert result["message"] == "Not found"
        assert result["status_code"] == 404

    def test_no_request_id_when_disabled(self):
        """Test request ID not included when disabled"""
        formatter = ErrorResponseFormatter(
            environment="production",
            include_request_id=False
        )

        request = Mock(spec=Request)
        request.state = Mock()
        request.state.request_id = "should-not-appear"

        exc = APIException(
            error_code=ErrorCode.SERVER_INTERNAL_ERROR,
            message="Error"
        )

        result = formatter.format_error(exc, request=request)

        assert "request_id" not in result

    def test_no_timestamp_when_disabled(self):
        """Test timestamp not included when disabled"""
        formatter = ErrorResponseFormatter(
            environment="production",
            include_timestamp=False
        )

        exc = APIException(
            error_code=ErrorCode.SERVER_INTERNAL_ERROR,
            message="Error"
        )

        result = formatter.format_error(exc)

        assert "timestamp" not in result

    def test_stack_trace_explicit_enable(self):
        """Test explicit stack trace enable"""
        formatter = ErrorResponseFormatter(
            environment="production",
            include_stack_trace=True  # Explicit override
        )

        exc = ValueError("Test error")
        result = formatter.format_error(exc)

        assert "stack_trace" in result

    def test_stack_trace_explicit_disable(self):
        """Test explicit stack trace disable"""
        formatter = ErrorResponseFormatter(
            environment="development",
            include_stack_trace=False  # Explicit override
        )

        exc = ValueError("Test error")
        result = formatter.format_error(exc)

        assert "stack_trace" not in result


# ============================================================================
# Test Exception Handlers
# ============================================================================

class TestExceptionHandlers:
    """Test exception handlers"""

    @pytest.mark.asyncio
    async def test_api_exception_handler(self):
        """Test API exception handler"""
        formatter = ErrorResponseFormatter(environment="production")
        handlers = create_exception_handlers(formatter=formatter)

        handler = handlers[APIException]

        # Mock request
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.request_id = "test-123"
        request.url = Mock()
        request.url.path = "/api/test"

        # Create exception
        exc = APIException(
            error_code=ErrorCode.AUTH_TOKEN_EXPIRED,
            message="Token expired"
        )

        response = await handler(request, exc)

        assert response.status_code == 401
        content = json.loads(response.body.decode())
        assert content["code"] == "AUTH_TOKEN_EXPIRED"

    @pytest.mark.asyncio
    async def test_http_exception_handler(self):
        """Test HTTP exception handler"""
        formatter = ErrorResponseFormatter(environment="production")
        handlers = create_exception_handlers(formatter=formatter)

        handler = handlers[StarletteHTTPException]

        # Mock request
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.request_id = "test-456"
        request.url = Mock()
        request.url.path = "/api/notfound"

        # Create exception
        exc = StarletteHTTPException(status_code=404, detail="Not found")

        response = await handler(request, exc)

        assert response.status_code == 404
        content = json.loads(response.body.decode())
        assert content["message"] == "Not found"

    @pytest.mark.asyncio
    async def test_generic_exception_handler(self):
        """Test generic exception handler"""
        formatter = ErrorResponseFormatter(environment="production")
        handlers = create_exception_handlers(formatter=formatter)

        handler = handlers[Exception]

        # Mock request
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.request_id = "test-789"
        request.url = Mock()
        request.url.path = "/api/error"

        # Create exception
        exc = ValueError("Unexpected error")

        response = await handler(request, exc)

        assert response.status_code == 500
        content = json.loads(response.body.decode())
        assert content["code"] == "SERVER_INTERNAL_ERROR"
        assert content["message"] == "An internal server error occurred"


# ============================================================================
# Test Setup Function
# ============================================================================

class TestSetupErrorHandling:
    """Test error handling setup"""

    def test_setup_production(self):
        """Test setup for production"""
        from fastapi import FastAPI

        app = FastAPI()
        formatter = setup_error_handling(app, environment="production")

        assert formatter.environment == "production"
        assert formatter.include_stack_trace is False

    def test_setup_development(self):
        """Test setup for development"""
        from fastapi import FastAPI

        app = FastAPI()
        formatter = setup_error_handling(app, environment="development")

        assert formatter.environment == "development"
        assert formatter.include_stack_trace is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
