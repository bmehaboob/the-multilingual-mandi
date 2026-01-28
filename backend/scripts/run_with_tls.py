#!/usr/bin/env python3
"""Run FastAPI server with TLS 1.3 for development

This script runs the Uvicorn server with TLS 1.3 enabled using self-signed certificates.
For production deployment, use Nginx with Let's Encrypt certificates instead.

Usage:
    python scripts/run_with_tls.py [--host HOST] [--port PORT]

Requirements:
    - Self-signed certificates in certs/ directory
    - Run generate_dev_certs.py first if certificates don't exist
"""
import argparse
import sys
from pathlib import Path
import uvicorn
from app.core.tls_config import get_uvicorn_ssl_config


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Run FastAPI server with TLS 1.3"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8443,
        help="Port to bind to (default: 8443)"
    )
    parser.add_argument(
        "--cert",
        default="certs/dev-cert.pem",
        help="Path to SSL certificate (default: certs/dev-cert.pem)"
    )
    parser.add_argument(
        "--key",
        default="certs/dev-key.pem",
        help="Path to SSL private key (default: certs/dev-key.pem)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes"
    )
    
    args = parser.parse_args()
    
    # Get backend directory
    backend_dir = Path(__file__).parent.parent
    cert_path = backend_dir / args.cert
    key_path = backend_dir / args.key
    
    # Check if certificates exist
    if not cert_path.exists() or not key_path.exists():
        print("❌ Error: SSL certificates not found!")
        print(f"\nCertificate: {cert_path}")
        print(f"Private Key: {key_path}")
        print("\n📝 Generate certificates first:")
        print("   python scripts/generate_dev_certs.py")
        return 1
    
    print("="*60)
    print("🔒 Starting FastAPI server with TLS 1.3")
    print("="*60)
    print(f"\nHost: {args.host}")
    print(f"Port: {args.port}")
    print(f"Certificate: {cert_path}")
    print(f"Private Key: {key_path}")
    print(f"Auto-reload: {args.reload}")
    print(f"\n🌐 Server URL: https://{args.host}:{args.port}")
    print(f"📚 API Docs: https://{args.host}:{args.port}/docs")
    print(f"💚 Health Check: https://{args.host}:{args.port}/health")
    print("\n⚠️  Using self-signed certificate - browser will show security warning")
    print("   Click 'Advanced' → 'Proceed to localhost' to continue")
    print("="*60 + "\n")
    
    try:
        # Get SSL configuration
        ssl_config = get_uvicorn_ssl_config(
            cert_file=str(cert_path),
            key_file=str(key_path)
        )
        
        # Run server
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            **ssl_config
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
        return 0
    except Exception as e:
        print(f"\n❌ Error starting server: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
