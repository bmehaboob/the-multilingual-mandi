"""TLS 1.3 Configuration for Multilingual Mandi API

This module provides TLS 1.3 configuration for secure HTTPS connections.
TLS configuration is applied at different levels:
- Development: Uvicorn with self-signed certificates
- Production: Nginx reverse proxy with Let's Encrypt certificates

Requirements: 15.1 - Encrypt all voice data during transmission using TLS 1.3 or higher
"""
import ssl
from pathlib import Path
from typing import Optional
from pydantic import BaseModel


class TLSConfig(BaseModel):
    """TLS configuration settings"""
    
    # Certificate paths
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    ca_file: Optional[str] = None
    
    # TLS version enforcement
    min_tls_version: str = "TLSv1.3"
    max_tls_version: str = "TLSv1.3"
    
    # Cipher suites (TLS 1.3 recommended ciphers)
    ciphers: str = (
        "TLS_AES_256_GCM_SHA384:"
        "TLS_AES_128_GCM_SHA256:"
        "TLS_CHACHA20_POLY1305_SHA256"
    )
    
    # Security options
    verify_mode: str = "CERT_REQUIRED"  # For client certificates (optional)
    check_hostname: bool = True
    
    # HSTS (HTTP Strict Transport Security)
    hsts_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 year in seconds
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True


def create_ssl_context(
    cert_file: str,
    key_file: str,
    ca_file: Optional[str] = None,
    min_version: int = ssl.TLSVersion.TLSv1_3,
    max_version: int = ssl.TLSVersion.TLSv1_3
) -> ssl.SSLContext:
    """
    Create an SSL context configured for TLS 1.3
    
    Args:
        cert_file: Path to SSL certificate file
        key_file: Path to SSL private key file
        ca_file: Optional path to CA certificate file
        min_version: Minimum TLS version (default: TLS 1.3)
        max_version: Maximum TLS version (default: TLS 1.3)
    
    Returns:
        Configured SSL context
    
    Raises:
        FileNotFoundError: If certificate or key files don't exist
        ssl.SSLError: If SSL context creation fails
    """
    # Verify files exist
    cert_path = Path(cert_file)
    key_path = Path(key_file)
    
    if not cert_path.exists():
        raise FileNotFoundError(f"Certificate file not found: {cert_file}")
    if not key_path.exists():
        raise FileNotFoundError(f"Key file not found: {key_file}")
    
    # Create SSL context with TLS 1.3
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    
    # Set minimum and maximum TLS versions
    context.minimum_version = min_version
    context.maximum_version = max_version
    
    # Load certificate and private key
    context.load_cert_chain(
        certfile=str(cert_path),
        keyfile=str(key_path)
    )
    
    # Load CA certificate if provided (for client certificate verification)
    if ca_file:
        ca_path = Path(ca_file)
        if ca_path.exists():
            context.load_verify_locations(cafile=str(ca_path))
            context.verify_mode = ssl.CERT_REQUIRED
        else:
            raise FileNotFoundError(f"CA certificate file not found: {ca_file}")
    
    # Set recommended cipher suites for TLS 1.3
    # Note: TLS 1.3 has a fixed set of cipher suites, but we can set preferences
    try:
        context.set_ciphers(
            "TLS_AES_256_GCM_SHA384:"
            "TLS_AES_128_GCM_SHA256:"
            "TLS_CHACHA20_POLY1305_SHA256"
        )
    except ssl.SSLError:
        # If specific ciphers fail, use default TLS 1.3 ciphers
        pass
    
    # Security options
    context.check_hostname = False  # Handled by reverse proxy in production
    context.options |= ssl.OP_NO_TLSv1    # Disable TLS 1.0
    context.options |= ssl.OP_NO_TLSv1_1  # Disable TLS 1.1
    context.options |= ssl.OP_NO_TLSv1_2  # Disable TLS 1.2 (enforce 1.3 only)
    context.options |= ssl.OP_NO_COMPRESSION  # Disable compression (CRIME attack)
    context.options |= ssl.OP_SINGLE_DH_USE   # Generate new DH key for each connection
    context.options |= ssl.OP_SINGLE_ECDH_USE # Generate new ECDH key for each connection
    
    return context


def get_uvicorn_ssl_config(
    cert_file: str,
    key_file: str,
    ca_file: Optional[str] = None
) -> dict:
    """
    Get SSL configuration for Uvicorn server
    
    Args:
        cert_file: Path to SSL certificate file
        key_file: Path to SSL private key file
        ca_file: Optional path to CA certificate file
    
    Returns:
        Dictionary with Uvicorn SSL configuration
    """
    config = {
        "ssl_certfile": cert_file,
        "ssl_keyfile": key_file,
        "ssl_version": ssl.PROTOCOL_TLS_SERVER,
        "ssl_cert_reqs": ssl.CERT_NONE,  # Client certificates not required by default
        "ssl_ca_certs": ca_file if ca_file else None,
    }
    
    # Create SSL context to enforce TLS 1.3
    ssl_context = create_ssl_context(cert_file, key_file, ca_file)
    config["ssl_context"] = ssl_context
    
    return config


def validate_tls_version(context: ssl.SSLContext) -> bool:
    """
    Validate that SSL context enforces TLS 1.3
    
    Args:
        context: SSL context to validate
    
    Returns:
        True if TLS 1.3 is enforced, False otherwise
    """
    return (
        context.minimum_version == ssl.TLSVersion.TLSv1_3 and
        context.maximum_version == ssl.TLSVersion.TLSv1_3
    )


def get_hsts_header(
    max_age: int = 31536000,
    include_subdomains: bool = True,
    preload: bool = True
) -> str:
    """
    Generate HTTP Strict Transport Security (HSTS) header value
    
    Args:
        max_age: Maximum age in seconds (default: 1 year)
        include_subdomains: Include subdomains in HSTS policy
        preload: Enable HSTS preload
    
    Returns:
        HSTS header value string
    """
    header = f"max-age={max_age}"
    
    if include_subdomains:
        header += "; includeSubDomains"
    
    if preload:
        header += "; preload"
    
    return header
