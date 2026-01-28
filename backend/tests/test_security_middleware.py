"""Unit tests for security middleware

Tests HTTPS enforcement, security headers, and HSTS configuration.

Requirements: 15.1 - Encrypt all voice data during transmission using TLS 1.3 or higher
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.middleware.security import (
    HTTPSRedirectMiddleware,
    SecurityHeadersMiddleware,
    TLSVersionCheckMiddleware
)


@pytest.fixture
def app():
    """Create a test FastAPI application"""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.get("/health")
    async def health_endpoint():
        return {"status": "healthy"}
    
    return app


class TestHTTPSRedirectMiddleware:
    """Test HTTPS redirect middleware"""
    
    def test_https_redirect_enabled(self, app):
        """Test that HTTP requests are redirected to HTTPS"""
        app.add_middleware(HTTPSRedirectMiddleware, enabled=True)
        client = TestClient(app, base_url="http://testserver")
        
        response = client.get("/test", follow_redirects=False)
        
        assert response.status_code == 301
        assert response.headers["location"].startswith("https://")
    
    def test_https_redirect_disabled(self, app):
        """Test that redirect can be disabled for development"""
        app.add_middleware(HTTPSRedirectMiddleware, enabled=False)
        client = TestClient(app, base_url="http://testserver")
        
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "test"}
    
    def test_https_request_not_redirected(self, app):
        """Test that HTTPS requests are not redirected"""
        app.add_middleware(HTTPSRedirectMiddleware, enabled=True)
        client = TestClient(app, base_url="https://testserver")
        
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "test"}


class TestSecurityHeadersMiddleware:
    """Test security headers middleware"""
    
    def test_hsts_header_on_https(self, app):
        """Test that HSTS header is added to HTTPS responses"""
        app.add_middleware(SecurityHeadersMiddleware, hsts_enabled=True)
        client = TestClient(app, base_url="https://testserver")
        
        response = client.get("/test")
        
        assert "Strict-Transport-Security" in response.headers
        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts
        assert "preload" in hsts
    
    def test_hsts_header_not_on_http(self, app):
        """Test that HSTS header is not added to HTTP responses"""
        app.add_middleware(SecurityHeadersMiddleware, hsts_enabled=True)
        client = TestClient(app, base_url="http://testserver")
        
        response = client.get("/test")
        
        # HSTS should not be present on HTTP
        assert "Strict-Transport-Security" not in response.headers
    
    def test_hsts_disabled(self, app):
        """Test that HSTS can be disabled"""
        app.add_middleware(SecurityHeadersMiddleware, hsts_enabled=False)
        client = TestClient(app, base_url="https://testserver")
        
        response = client.get("/test")
        
        assert "Strict-Transport-Security" not in response.headers
    
    def test_custom_hsts_settings(self, app):
        """Test custom HSTS settings"""
        app.add_middleware(
            SecurityHeadersMiddleware,
            hsts_enabled=True,
            hsts_max_age=86400,
            hsts_include_subdomains=False,
            hsts_preload=False
        )
        client = TestClient(app, base_url="https://testserver")
        
        response = client.get("/test")
        
        hsts = response.headers["Strict-Transport-Security"]
        assert hsts == "max-age=86400"
    
    def test_x_content_type_options_header(self, app):
        """Test X-Content-Type-Options header"""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    def test_x_frame_options_header(self, app):
        """Test X-Frame-Options header"""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.headers["X-Frame-Options"] == "DENY"
    
    def test_x_xss_protection_header(self, app):
        """Test X-XSS-Protection header"""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
    
    def test_referrer_policy_header(self, app):
        """Test Referrer-Policy header"""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    
    def test_content_security_policy_header(self, app):
        """Test Content-Security-Policy header"""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
    
    def test_permissions_policy_header(self, app):
        """Test Permissions-Policy header"""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert "Permissions-Policy" in response.headers
        policy = response.headers["Permissions-Policy"]
        assert "geolocation=()" in policy
        assert "microphone=(self)" in policy
    
    def test_all_security_headers_present(self, app):
        """Test that all security headers are present"""
        app.add_middleware(SecurityHeadersMiddleware, hsts_enabled=True)
        client = TestClient(app, base_url="https://testserver")
        
        response = client.get("/test")
        
        # Check all expected headers
        expected_headers = [
            "Strict-Transport-Security",
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Content-Security-Policy",
            "Permissions-Policy"
        ]
        
        for header in expected_headers:
            assert header in response.headers, f"Missing header: {header}"


class TestTLSVersionCheckMiddleware:
    """Test TLS version check middleware"""
    
    def test_tls_version_header_captured(self, app):
        """Test that TLS version from header is captured"""
        app.add_middleware(TLSVersionCheckMiddleware)
        client = TestClient(app)
        
        response = client.get(
            "/test",
            headers={"X-TLS-Version": "TLSv1.3"}
        )
        
        assert response.status_code == 200
    
    def test_no_tls_version_header(self, app):
        """Test that middleware works without TLS version header"""
        app.add_middleware(TLSVersionCheckMiddleware)
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.status_code == 200


class TestMiddlewareIntegration:
    """Integration tests for multiple middleware"""
    
    def test_all_middleware_together(self, app):
        """Test all security middleware working together"""
        # Add all middleware
        app.add_middleware(TLSVersionCheckMiddleware)
        app.add_middleware(SecurityHeadersMiddleware, hsts_enabled=True)
        app.add_middleware(HTTPSRedirectMiddleware, enabled=False)
        
        client = TestClient(app, base_url="https://testserver")
        
        response = client.get("/test")
        
        # Check response is successful
        assert response.status_code == 200
        assert response.json() == {"message": "test"}
        
        # Check security headers are present
        assert "Strict-Transport-Security" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
    
    def test_middleware_order_matters(self, app):
        """Test that middleware order is correct"""
        # HTTPS redirect should be first (outermost)
        # Security headers should be last (innermost)
        app.add_middleware(SecurityHeadersMiddleware, hsts_enabled=True)
        app.add_middleware(HTTPSRedirectMiddleware, enabled=True)
        
        # HTTP request should be redirected before headers are added
        client = TestClient(app, base_url="http://testserver")
        response = client.get("/test", follow_redirects=False)
        
        assert response.status_code == 301
        
        # HTTPS request should get security headers
        client_https = TestClient(app, base_url="https://testserver")
        response_https = client_https.get("/test")
        
        assert response_https.status_code == 200
        assert "Strict-Transport-Security" in response_https.headers


class TestSecurityHeadersValues:
    """Test specific security header values"""
    
    def test_hsts_max_age_one_year(self, app):
        """Test HSTS max-age is set to 1 year (31536000 seconds)"""
        app.add_middleware(SecurityHeadersMiddleware, hsts_enabled=True)
        client = TestClient(app, base_url="https://testserver")
        
        response = client.get("/test")
        
        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=31536000" in hsts
    
    def test_csp_allows_microphone(self, app):
        """Test CSP allows microphone for voice input"""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)
        
        response = client.get("/test")
        
        csp = response.headers["Content-Security-Policy"]
        assert "media-src 'self' blob:" in csp
    
    def test_permissions_policy_allows_microphone(self, app):
        """Test Permissions-Policy allows microphone for voice input"""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)
        
        response = client.get("/test")
        
        policy = response.headers["Permissions-Policy"]
        assert "microphone=(self)" in policy
    
    def test_frame_options_deny(self, app):
        """Test X-Frame-Options is set to DENY to prevent clickjacking"""
        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.headers["X-Frame-Options"] == "DENY"
