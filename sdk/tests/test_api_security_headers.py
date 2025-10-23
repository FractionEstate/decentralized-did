"""
Tests for API Security Headers Middleware

Tests security headers functionality including:
- HSTS (HTTP Strict Transport Security)
- CSP (Content Security Policy)
- Frame options
- Content type options
- Referrer policy
- Permissions policy
- XSS protection
- CORS configuration
- HTTPS enforcement

License: Open-source (MIT)
"""

from src.decentralized_did.api.security_headers import (
    SecurityHeadersConfig,
    SecurityHeadersMiddleware,
    CORSConfig,
    setup_security_headers,
    setup_cors,
    setup_all_security,
)
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import FastAPI, Request, Response
from starlette.responses import JSONResponse

# Import security headers module
import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


# ============================================================================
# Test Security Headers Config
# ============================================================================

class TestSecurityHeadersConfig:
    """Test security headers configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = SecurityHeadersConfig()

        assert config.enable_hsts is True
        assert config.hsts_max_age == 31536000
        assert config.hsts_include_subdomains is True
        assert config.hsts_preload is False

        assert config.enable_csp is True
        assert config.csp_default_src == ["'self'"]
        assert config.csp_script_src == ["'self'"]

        assert config.enable_frame_options is True
        assert config.frame_options == "DENY"

        assert config.enable_content_type_options is True
        assert config.enable_referrer_policy is True
        assert config.enable_permissions_policy is True
        assert config.enable_xss_protection is True

        assert config.enforce_https is False

    def test_production_config(self):
        """Test production configuration"""
        config = SecurityHeadersConfig.production_config()

        assert config.enable_hsts is True
        assert config.hsts_max_age == 31536000
        assert config.hsts_include_subdomains is True
        assert config.hsts_preload is True

        assert config.frame_options == "DENY"
        assert config.referrer_policy == "strict-origin-when-cross-origin"
        assert config.enforce_https is True

    def test_development_config(self):
        """Test development configuration"""
        config = SecurityHeadersConfig.development_config()

        assert config.enable_hsts is False  # No HTTPS enforcement in dev
        assert config.frame_options == "SAMEORIGIN"
        assert config.enforce_https is False

        # More relaxed CSP for dev
        assert "'unsafe-inline'" in config.csp_script_src
        assert "'unsafe-eval'" in config.csp_script_src

    def test_custom_config(self):
        """Test custom configuration values"""
        config = SecurityHeadersConfig(
            enable_hsts=False,
            hsts_max_age=7200,
            frame_options="SAMEORIGIN",
            csp_default_src=["'none'"],
            enforce_https=True,
        )

        assert config.enable_hsts is False
        assert config.hsts_max_age == 7200
        assert config.frame_options == "SAMEORIGIN"
        assert config.csp_default_src == ["'none'"]
        assert config.enforce_https is True


# ============================================================================
# Test HSTS Header
# ============================================================================

class TestHSTSHeader:
    """Test HTTP Strict Transport Security header"""

    @pytest.mark.asyncio
    async def test_hsts_basic(self):
        """Test basic HSTS header"""
        config = SecurityHeadersConfig(
            enable_hsts=True,
            hsts_max_age=31536000,
            hsts_include_subdomains=False  # Disable subdomains for this test
        )
        middleware = SecurityHeadersMiddleware(None, config)

        response = Response()
        middleware._add_hsts_header(response)

        assert "Strict-Transport-Security" in response.headers
        assert response.headers["Strict-Transport-Security"] == "max-age=31536000"

    @pytest.mark.asyncio
    async def test_hsts_with_subdomains(self):
        """Test HSTS header with includeSubDomains"""
        config = SecurityHeadersConfig(
            enable_hsts=True,
            hsts_max_age=31536000,
            hsts_include_subdomains=True
        )
        middleware = SecurityHeadersMiddleware(None, config)

        response = Response()
        middleware._add_hsts_header(response)

        assert "includeSubDomains" in response.headers["Strict-Transport-Security"]

    @pytest.mark.asyncio
    async def test_hsts_with_preload(self):
        """Test HSTS header with preload"""
        config = SecurityHeadersConfig(
            enable_hsts=True,
            hsts_max_age=31536000,
            hsts_include_subdomains=True,
            hsts_preload=True
        )
        middleware = SecurityHeadersMiddleware(None, config)

        response = Response()
        middleware._add_hsts_header(response)

        header = response.headers["Strict-Transport-Security"]
        assert "max-age=31536000" in header
        assert "includeSubDomains" in header
        assert "preload" in header

    @pytest.mark.asyncio
    async def test_hsts_disabled(self):
        """Test HSTS header when disabled"""
        config = SecurityHeadersConfig(enable_hsts=False)
        middleware = SecurityHeadersMiddleware(None, config)

        response = Response()
        middleware._add_hsts_header(response)

        assert "Strict-Transport-Security" not in response.headers


# ============================================================================
# Test CSP Header
# ============================================================================

class TestCSPHeader:
    """Test Content Security Policy header"""

    @pytest.mark.asyncio
    async def test_csp_basic(self):
        """Test basic CSP header"""
        config = SecurityHeadersConfig(
            enable_csp=True,
            csp_default_src=["'self'"],
            csp_script_src=["'self'"],
        )
        middleware = SecurityHeadersMiddleware(None, config)

        response = Response()
        middleware._add_csp_header(response)

        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp

    @pytest.mark.asyncio
    async def test_csp_multiple_sources(self):
        """Test CSP with multiple sources"""
        config = SecurityHeadersConfig(
            enable_csp=True,
            csp_script_src=["'self'", "https://cdn.example.com"],
            csp_style_src=["'self'", "'unsafe-inline'"],
        )
        middleware = SecurityHeadersMiddleware(None, config)

        response = Response()
        middleware._add_csp_header(response)

        csp = response.headers["Content-Security-Policy"]
        assert "script-src 'self' https://cdn.example.com" in csp
        assert "style-src 'self' 'unsafe-inline'" in csp

    @pytest.mark.asyncio
    async def test_csp_with_report_uri(self):
        """Test CSP with report URI"""
        config = SecurityHeadersConfig(
            enable_csp=True,
            csp_default_src=["'self'"],
            csp_report_uri="https://example.com/csp-report"
        )
        middleware = SecurityHeadersMiddleware(None, config)

        response = Response()
        middleware._add_csp_header(response)

        csp = response.headers["Content-Security-Policy"]
        assert "report-uri https://example.com/csp-report" in csp

    @pytest.mark.asyncio
    async def test_csp_disabled(self):
        """Test CSP when disabled"""
        config = SecurityHeadersConfig(enable_csp=False)
        middleware = SecurityHeadersMiddleware(None, config)

        response = Response()
        middleware._add_csp_header(response)

        assert "Content-Security-Policy" not in response.headers


# ============================================================================
# Test Other Security Headers
# ============================================================================

class TestOtherHeaders:
    """Test other security headers"""

    @pytest.mark.asyncio
    async def test_frame_options_deny(self):
        """Test X-Frame-Options: DENY"""
        config = SecurityHeadersConfig(
            enable_frame_options=True,
            frame_options="DENY"
        )
        middleware = SecurityHeadersMiddleware(None, config)

        response = Response()
        middleware._add_frame_options_header(response)

        assert response.headers["X-Frame-Options"] == "DENY"

    @pytest.mark.asyncio
    async def test_frame_options_sameorigin(self):
        """Test X-Frame-Options: SAMEORIGIN"""
        config = SecurityHeadersConfig(
            enable_frame_options=True,
            frame_options="SAMEORIGIN"
        )
        middleware = SecurityHeadersMiddleware(None, config)

        response = Response()
        middleware._add_frame_options_header(response)

        assert response.headers["X-Frame-Options"] == "SAMEORIGIN"

    @pytest.mark.asyncio
    async def test_content_type_options(self):
        """Test X-Content-Type-Options header"""
        config = SecurityHeadersConfig(enable_content_type_options=True)
        middleware = SecurityHeadersMiddleware(None, config)

        response = Response()
        middleware._add_content_type_options_header(response)

        assert response.headers["X-Content-Type-Options"] == "nosniff"

    @pytest.mark.asyncio
    async def test_referrer_policy(self):
        """Test Referrer-Policy header"""
        config = SecurityHeadersConfig(
            enable_referrer_policy=True,
            referrer_policy="strict-origin-when-cross-origin"
        )
        middleware = SecurityHeadersMiddleware(None, config)

        response = Response()
        middleware._add_referrer_policy_header(response)

        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_permissions_policy(self):
        """Test Permissions-Policy header"""
        config = SecurityHeadersConfig(
            enable_permissions_policy=True,
            permissions_policy={
                "geolocation": ["()"],
                "microphone": ["()"],
                "camera": ["()"],
            }
        )
        middleware = SecurityHeadersMiddleware(None, config)

        response = Response()
        middleware._add_permissions_policy_header(response)

        policy = response.headers["Permissions-Policy"]
        assert "geolocation=()" in policy
        assert "microphone=()" in policy
        assert "camera=()" in policy

    @pytest.mark.asyncio
    async def test_xss_protection(self):
        """Test X-XSS-Protection header"""
        config = SecurityHeadersConfig(enable_xss_protection=True)
        middleware = SecurityHeadersMiddleware(None, config)

        response = Response()
        middleware._add_xss_protection_header(response)

        assert response.headers["X-XSS-Protection"] == "1; mode=block"


# ============================================================================
# Test HTTPS Enforcement
# ============================================================================

class TestHTTPSEnforcement:
    """Test HTTPS enforcement (HTTP → HTTPS redirect)"""

    @pytest.mark.asyncio
    async def test_https_redirect(self):
        """Test HTTP to HTTPS redirect"""
        config = SecurityHeadersConfig(enforce_https=True, https_port=443)

        # Mock request
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.scheme = "http"
        request.url.replace = Mock(return_value="https://example.com/api/test")

        # Mock call_next
        call_next = AsyncMock()

        middleware = SecurityHeadersMiddleware(None, config)
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 301
        assert "Location" in response.headers
        assert response.headers["Location"] == "https://example.com/api/test"

        # call_next should NOT be called
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_https_already_secure(self):
        """Test HTTPS request passes through"""
        config = SecurityHeadersConfig(enforce_https=True)

        # Mock HTTPS request
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.scheme = "https"

        # Mock call_next
        mock_response = JSONResponse({"status": "ok"})
        call_next = AsyncMock(return_value=mock_response)

        middleware = SecurityHeadersMiddleware(None, config)
        response = await middleware.dispatch(request, call_next)

        # call_next should be called
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_https_enforcement_disabled(self):
        """Test HTTPS enforcement disabled"""
        config = SecurityHeadersConfig(enforce_https=False)

        # Mock HTTP request
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.scheme = "http"

        # Mock call_next
        mock_response = JSONResponse({"status": "ok"})
        call_next = AsyncMock(return_value=mock_response)

        middleware = SecurityHeadersMiddleware(None, config)
        response = await middleware.dispatch(request, call_next)

        # call_next should be called (no redirect)
        call_next.assert_called_once()


# ============================================================================
# Test CORS Configuration
# ============================================================================

class TestCORSConfig:
    """Test CORS configuration"""

    def test_default_cors_config(self):
        """Test default CORS configuration"""
        config = CORSConfig()

        assert config.allow_origins == ["*"]
        assert config.allow_methods == [
            "GET", "POST", "PUT", "DELETE", "OPTIONS"]
        assert config.allow_headers == ["*"]
        assert config.allow_credentials is False
        assert config.max_age == 600

    def test_production_cors_config(self):
        """Test production CORS configuration"""
        allowed = ["https://wallet.example.com", "https://app.example.com"]
        config = CORSConfig.production_config(allowed)

        assert config.allow_origins == allowed
        assert "Authorization" in config.allow_headers
        assert "X-API-Key" in config.allow_headers
        assert config.allow_credentials is True

    def test_development_cors_config(self):
        """Test development CORS configuration"""
        config = CORSConfig.development_config()

        assert config.allow_origins == ["*"]
        assert config.allow_methods == ["*"]
        assert config.allow_headers == ["*"]
        assert config.allow_credentials is False

    def test_custom_cors_config(self):
        """Test custom CORS configuration"""
        config = CORSConfig(
            allow_origins=["https://example.com"],
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
            allow_credentials=True,
            max_age=1200,
        )

        assert config.allow_origins == ["https://example.com"]
        assert config.allow_methods == ["GET", "POST"]
        assert config.allow_headers == ["Content-Type"]
        assert config.allow_credentials is True
        assert config.max_age == 1200


# ============================================================================
# Test Setup Functions
# ============================================================================

class TestSetupFunctions:
    """Test setup helper functions"""

    def test_setup_security_headers_production(self):
        """Test setup_security_headers for production"""
        app = FastAPI()
        setup_security_headers(app, environment="production")

        # Check middleware was added
        assert any(
            hasattr(m, 'cls') and m.cls == SecurityHeadersMiddleware
            for m in app.user_middleware
        )

    def test_setup_security_headers_development(self):
        """Test setup_security_headers for development"""
        app = FastAPI()
        setup_security_headers(app, environment="development")

        # Check middleware was added
        assert any(
            hasattr(m, 'cls') and m.cls == SecurityHeadersMiddleware
            for m in app.user_middleware
        )

    def test_setup_security_headers_custom(self):
        """Test setup_security_headers with custom config"""
        app = FastAPI()
        config = SecurityHeadersConfig(enable_hsts=False)
        setup_security_headers(app, config=config)

        # Check middleware was added
        assert any(
            hasattr(m, 'cls') and m.cls == SecurityHeadersMiddleware
            for m in app.user_middleware
        )

    def test_setup_cors_production(self):
        """Test setup_cors for production"""
        app = FastAPI()
        setup_cors(
            app,
            environment="production",
            allowed_origins=["https://example.com"]
        )

        # Check CORS middleware was added
        # (CORSMiddleware from FastAPI/Starlette)
        assert len(app.user_middleware) > 0

    def test_setup_cors_development(self):
        """Test setup_cors for development"""
        app = FastAPI()
        setup_cors(app, environment="development")

        # Check CORS middleware was added
        assert len(app.user_middleware) > 0

    def test_setup_cors_production_requires_origins(self):
        """Test setup_cors for production requires allowed_origins"""
        app = FastAPI()

        with pytest.raises(ValueError, match="allowed_origins required"):
            setup_cors(app, environment="production")

    def test_setup_all_security_production(self):
        """Test setup_all_security for production"""
        app = FastAPI()
        setup_all_security(
            app,
            environment="production",
            allowed_origins=["https://example.com"]
        )

        # Check both middlewares were added
        assert len(app.user_middleware) >= 2

    def test_setup_all_security_development(self):
        """Test setup_all_security for development"""
        app = FastAPI()
        setup_all_security(app, environment="development")

        # Check both middlewares were added
        assert len(app.user_middleware) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
