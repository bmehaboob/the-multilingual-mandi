"""Security middleware for HTTPS enforcement and security headers

This middleware enforces HTTPS connections and adds security headers
including HSTS (HTTP Strict Transport Security).

Requirements: 15.1 - Encrypt all voice data during transmission using TLS 1.3 or higher
"""
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
from app.core.tls_config import get_hsts_header


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Middleware to redirect HTTP requests to HTTPS"""
    
    def __init__(self, app: ASGIApp, enabled: bool = True):
        """
        Initialize HTTPS redirect middleware
        
        Args:
            app: ASGI application
            enabled: Whether to enforce HTTPS redirects (disable for local dev)
        """
        super().__init__(app)
        self.enabled = enabled
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Redirect HTTP requests to HTTPS
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
        
        Returns:
            Response (redirect if HTTP, normal response if HTTPS)
        """
        # Skip redirect if disabled (e.g., local development)
        if not self.enabled:
            return await call_next(request)
        
        # Check if request is HTTP (not HTTPS)
        if request.url.scheme == "http":
            # Build HTTPS URL
            https_url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(https_url), status_code=301)
        
        # Request is already HTTPS, proceed normally
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    def __init__(
        self,
        app: ASGIApp,
        hsts_enabled: bool = True,
        hsts_max_age: int = 31536000,
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = True
    ):
        """
        Initialize security headers middleware
        
        Args:
            app: ASGI application
            hsts_enabled: Enable HSTS header
            hsts_max_age: HSTS max age in seconds
            hsts_include_subdomains: Include subdomains in HSTS
            hsts_preload: Enable HSTS preload
        """
        super().__init__(app)
        self.hsts_enabled = hsts_enabled
        self.hsts_header = get_hsts_header(
            max_age=hsts_max_age,
            include_subdomains=hsts_include_subdomains,
            preload=hsts_preload
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add security headers to response
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
        
        Returns:
            Response with security headers added
        """
        response = await call_next(request)
        
        # Add HSTS header (only for HTTPS connections)
        if self.hsts_enabled and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = self.hsts_header
        
        # Add other security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy (adjust as needed for your frontend)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "media-src 'self' blob:; "
            "worker-src 'self' blob:;"
        )
        
        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(self), "
            "camera=(), "
            "payment=(), "
            "usb=()"
        )
        
        return response


class TLSVersionCheckMiddleware(BaseHTTPMiddleware):
    """Middleware to log TLS version information (for monitoring)"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log TLS version information
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
        
        Returns:
            Response
        """
        # Get TLS version from request scope if available
        # Note: This information is typically available when using a reverse proxy
        # that sets appropriate headers (e.g., X-Forwarded-Proto, X-TLS-Version)
        
        tls_version = request.headers.get("X-TLS-Version")
        if tls_version:
            # Log TLS version for monitoring
            # In production, this would go to your logging system
            request.state.tls_version = tls_version
        
        response = await call_next(request)
        return response
