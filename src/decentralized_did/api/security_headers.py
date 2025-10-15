"""
Security Headers Middleware for API Servers

Provides comprehensive security headers:
- HSTS (HTTP Strict Transport Security)
- CSP (Content Security Policy)
- X-Frame-Options (clickjacking prevention)
- X-Content-Type-Options (MIME sniffing prevention)
- Referrer-Policy (referrer control)
- Permissions-Policy (feature control)
- CORS (Cross-Origin Resource Sharing)
- HTTPS enforcement

License: Open-source (MIT)
"""

from typing import Optional, Dict, List, Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Security Headers Configuration
# ============================================================================

class SecurityHeadersConfig:
    """Configuration for security headers"""

    def __init__(
        self,
        # HSTS
        enable_hsts: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,

        # CSP
        enable_csp: bool = True,
        csp_default_src: Optional[List[str]] = None,
        csp_script_src: Optional[List[str]] = None,
        csp_style_src: Optional[List[str]] = None,
        csp_img_src: Optional[List[str]] = None,
        csp_connect_src: Optional[List[str]] = None,
        csp_report_uri: Optional[str] = None,

        # Frame options
        enable_frame_options: bool = True,
        frame_options: str = "DENY",  # DENY, SAMEORIGIN, ALLOW-FROM

        # Content type options
        enable_content_type_options: bool = True,

        # Referrer policy
        enable_referrer_policy: bool = True,
        referrer_policy: str = "strict-origin-when-cross-origin",

        # Permissions policy
        enable_permissions_policy: bool = True,
        permissions_policy: Optional[Dict[str, List[str]]] = None,

        # XSS protection (legacy, but still useful)
        enable_xss_protection: bool = True,

        # HTTPS enforcement
        enforce_https: bool = False,
        https_port: int = 443,
    ):
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload

        self.enable_csp = enable_csp
        self.csp_default_src = csp_default_src or ["'self'"]
        self.csp_script_src = csp_script_src or ["'self'"]
        self.csp_style_src = csp_style_src or ["'self'"]
        self.csp_img_src = csp_img_src or ["'self'", "data:", "https:"]
        self.csp_connect_src = csp_connect_src or ["'self'"]
        self.csp_report_uri = csp_report_uri

        self.enable_frame_options = enable_frame_options
        self.frame_options = frame_options

        self.enable_content_type_options = enable_content_type_options

        self.enable_referrer_policy = enable_referrer_policy
        self.referrer_policy = referrer_policy

        self.enable_permissions_policy = enable_permissions_policy
        self.permissions_policy = permissions_policy or {
            "geolocation": ["()"],
            "microphone": ["()"],
            "camera": ["()"],
        }

        self.enable_xss_protection = enable_xss_protection

        self.enforce_https = enforce_https
        self.https_port = https_port

    @classmethod
    def production_config(cls) -> "SecurityHeadersConfig":
        """Get production-grade security configuration"""
        return cls(
            enable_hsts=True,
            hsts_max_age=31536000,  # 1 year
            hsts_include_subdomains=True,
            hsts_preload=True,
            enable_csp=True,
            csp_default_src=["'self'"],
            csp_script_src=["'self'"],
            # Allow inline styles for API docs
            csp_style_src=["'self'", "'unsafe-inline'"],
            csp_img_src=["'self'", "data:", "https:"],
            csp_connect_src=["'self'"],
            enable_frame_options=True,
            frame_options="DENY",
            enable_content_type_options=True,
            enable_referrer_policy=True,
            referrer_policy="strict-origin-when-cross-origin",
            enable_permissions_policy=True,
            enable_xss_protection=True,
            enforce_https=True,
        )

    @classmethod
    def development_config(cls) -> "SecurityHeadersConfig":
        """Get development-friendly configuration"""
        return cls(
            enable_hsts=False,  # Don't enforce HTTPS in dev
            enable_csp=True,
            csp_default_src=["'self'"],
            csp_script_src=["'self'", "'unsafe-inline'",
                            "'unsafe-eval'"],  # Relaxed for dev
            csp_style_src=["'self'", "'unsafe-inline'"],
            csp_img_src=["'self'", "data:", "http:", "https:"],
            csp_connect_src=["'self'", "http:", "https:"],
            enable_frame_options=True,
            frame_options="SAMEORIGIN",
            enable_content_type_options=True,
            enable_referrer_policy=True,
            referrer_policy="no-referrer-when-downgrade",
            enable_permissions_policy=True,
            enable_xss_protection=True,
            enforce_https=False,
        )


# ============================================================================
# Security Headers Middleware
# ============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses

    Features:
    - HSTS (HTTP Strict Transport Security)
    - CSP (Content Security Policy)
    - X-Frame-Options (clickjacking prevention)
    - X-Content-Type-Options (MIME sniffing prevention)
    - Referrer-Policy
    - Permissions-Policy
    - X-XSS-Protection (legacy)
    - HTTPS enforcement
    """

    def __init__(self, app: ASGIApp, config: SecurityHeadersConfig):
        super().__init__(app)
        self.config = config

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""

        # Check HTTPS enforcement
        if self.config.enforce_https:
            if request.url.scheme != "https":
                # Redirect to HTTPS
                https_url = request.url.replace(
                    scheme="https",
                    port=self.config.https_port
                )
                logger.warning(
                    f"HTTPS enforcement: redirecting {request.url} to {https_url}"
                )
                return Response(
                    status_code=301,
                    headers={"Location": str(https_url)}
                )

        # Process request
        response = await call_next(request)

        # Add security headers
        self._add_hsts_header(response)
        self._add_csp_header(response)
        self._add_frame_options_header(response)
        self._add_content_type_options_header(response)
        self._add_referrer_policy_header(response)
        self._add_permissions_policy_header(response)
        self._add_xss_protection_header(response)

        return response

    def _add_hsts_header(self, response: Response) -> None:
        """Add HTTP Strict Transport Security header"""
        if not self.config.enable_hsts:
            return

        value = f"max-age={self.config.hsts_max_age}"

        if self.config.hsts_include_subdomains:
            value += "; includeSubDomains"

        if self.config.hsts_preload:
            value += "; preload"

        response.headers["Strict-Transport-Security"] = value

    def _add_csp_header(self, response: Response) -> None:
        """Add Content Security Policy header"""
        if not self.config.enable_csp:
            return

        directives = []

        # Default source
        if self.config.csp_default_src:
            directives.append(
                f"default-src {' '.join(self.config.csp_default_src)}"
            )

        # Script source
        if self.config.csp_script_src:
            directives.append(
                f"script-src {' '.join(self.config.csp_script_src)}"
            )

        # Style source
        if self.config.csp_style_src:
            directives.append(
                f"style-src {' '.join(self.config.csp_style_src)}"
            )

        # Image source
        if self.config.csp_img_src:
            directives.append(
                f"img-src {' '.join(self.config.csp_img_src)}"
            )

        # Connect source (API calls)
        if self.config.csp_connect_src:
            directives.append(
                f"connect-src {' '.join(self.config.csp_connect_src)}"
            )

        # Report URI
        if self.config.csp_report_uri:
            directives.append(f"report-uri {self.config.csp_report_uri}")

        response.headers["Content-Security-Policy"] = "; ".join(directives)

    def _add_frame_options_header(self, response: Response) -> None:
        """Add X-Frame-Options header (clickjacking prevention)"""
        if not self.config.enable_frame_options:
            return

        response.headers["X-Frame-Options"] = self.config.frame_options

    def _add_content_type_options_header(self, response: Response) -> None:
        """Add X-Content-Type-Options header (MIME sniffing prevention)"""
        if not self.config.enable_content_type_options:
            return

        response.headers["X-Content-Type-Options"] = "nosniff"

    def _add_referrer_policy_header(self, response: Response) -> None:
        """Add Referrer-Policy header"""
        if not self.config.enable_referrer_policy:
            return

        response.headers["Referrer-Policy"] = self.config.referrer_policy

    def _add_permissions_policy_header(self, response: Response) -> None:
        """Add Permissions-Policy header (feature control)"""
        if not self.config.enable_permissions_policy:
            return

        # Format: feature=(allowed-origins)
        policies = []
        for feature, origins in self.config.permissions_policy.items():
            origins_str = " ".join(origins)
            policies.append(f"{feature}={origins_str}")

        response.headers["Permissions-Policy"] = ", ".join(policies)

    def _add_xss_protection_header(self, response: Response) -> None:
        """Add X-XSS-Protection header (legacy, but still useful)"""
        if not self.config.enable_xss_protection:
            return

        response.headers["X-XSS-Protection"] = "1; mode=block"


# ============================================================================
# CORS Configuration
# ============================================================================

class CORSConfig:
    """Configuration for CORS (Cross-Origin Resource Sharing)"""

    def __init__(
        self,
        allow_origins: Optional[List[str]] = None,
        allow_methods: Optional[List[str]] = None,
        allow_headers: Optional[List[str]] = None,
        allow_credentials: bool = False,
        max_age: int = 600,  # 10 minutes
    ):
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or [
            "GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
        self.max_age = max_age

    @classmethod
    def production_config(cls, allowed_origins: List[str]) -> "CORSConfig":
        """Get production CORS configuration"""
        return cls(
            allow_origins=allowed_origins,  # Specific origins only
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-API-Key"],
            allow_credentials=True,
            max_age=600,
        )

    @classmethod
    def development_config(cls) -> "CORSConfig":
        """Get development CORS configuration"""
        return cls(
            allow_origins=["*"],  # Allow all in dev
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=False,
            max_age=600,
        )


# ============================================================================
# Setup Functions
# ============================================================================

def setup_security_headers(
    app: FastAPI,
    config: Optional[SecurityHeadersConfig] = None,
    environment: str = "production"
) -> None:
    """
    Add security headers middleware to FastAPI app

    Args:
        app: FastAPI application
        config: Security headers configuration (optional)
        environment: "production" or "development"

    Example:
        >>> app = FastAPI()
        >>> setup_security_headers(app, environment="production")
    """
    if config is None:
        if environment == "production":
            config = SecurityHeadersConfig.production_config()
        else:
            config = SecurityHeadersConfig.development_config()

    app.add_middleware(SecurityHeadersMiddleware, config=config)
    logger.info(f"Security headers middleware configured for {environment}")


def setup_cors(
    app: FastAPI,
    config: Optional[CORSConfig] = None,
    environment: str = "production",
    allowed_origins: Optional[List[str]] = None
) -> None:
    """
    Add CORS middleware to FastAPI app

    Args:
        app: FastAPI application
        config: CORS configuration (optional)
        environment: "production" or "development"
        allowed_origins: List of allowed origins for production (optional)

    Example:
        >>> app = FastAPI()
        >>> setup_cors(app, environment="production", allowed_origins=["https://example.com"])
    """
    if config is None:
        if environment == "production":
            if allowed_origins is None:
                raise ValueError(
                    "allowed_origins required for production CORS")
            config = CORSConfig.production_config(allowed_origins)
        else:
            config = CORSConfig.development_config()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allow_origins,
        allow_credentials=config.allow_credentials,
        allow_methods=config.allow_methods,
        allow_headers=config.allow_headers,
        max_age=config.max_age,
    )
    logger.info(f"CORS middleware configured for {environment}")


def setup_all_security(
    app: FastAPI,
    environment: str = "production",
    security_config: Optional[SecurityHeadersConfig] = None,
    cors_config: Optional[CORSConfig] = None,
    allowed_origins: Optional[List[str]] = None
) -> None:
    """
    Setup all security features (headers + CORS)

    Args:
        app: FastAPI application
        environment: "production" or "development"
        security_config: Security headers configuration (optional)
        cors_config: CORS configuration (optional)
        allowed_origins: Allowed origins for production CORS (optional)

    Example:
        >>> app = FastAPI()
        >>> setup_all_security(
        ...     app,
        ...     environment="production",
        ...     allowed_origins=["https://wallet.example.com"]
        ... )
    """
    setup_cors(app, cors_config, environment, allowed_origins)
    setup_security_headers(app, security_config, environment)
    logger.info(f"All security features configured for {environment}")
