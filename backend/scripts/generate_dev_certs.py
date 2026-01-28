#!/usr/bin/env python3
"""Generate self-signed SSL certificates for development

This script generates self-signed SSL certificates for local development and testing.
DO NOT use these certificates in production - use Let's Encrypt or a proper CA instead.

Usage:
    python scripts/generate_dev_certs.py

Output:
    - certs/dev-cert.pem (certificate)
    - certs/dev-key.pem (private key)
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


def generate_self_signed_cert(
    output_dir: Path,
    cert_name: str = "dev-cert.pem",
    key_name: str = "dev-key.pem",
    common_name: str = "localhost",
    validity_days: int = 365
):
    """
    Generate a self-signed SSL certificate for development
    
    Args:
        output_dir: Directory to save certificate and key
        cert_name: Certificate filename
        key_name: Private key filename
        common_name: Common name for certificate (e.g., localhost)
        validity_days: Certificate validity period in days
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating self-signed certificate for {common_name}...")
    
    # Generate private key
    print("Generating RSA private key (2048 bits)...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Create certificate subject
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Maharashtra"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Mumbai"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Multilingual Mandi Dev"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    
    # Create certificate
    print("Creating certificate...")
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=validity_days))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
                x509.DNSName("::1"),
            ]),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
            ]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256(), default_backend())
    )
    
    # Write private key to file
    key_path = output_dir / key_name
    print(f"Writing private key to {key_path}...")
    with open(key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
        )
    
    # Set restrictive permissions on private key
    os.chmod(key_path, 0o600)
    
    # Write certificate to file
    cert_path = output_dir / cert_name
    print(f"Writing certificate to {cert_path}...")
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    print("\n" + "="*60)
    print("✓ Self-signed certificate generated successfully!")
    print("="*60)
    print(f"\nCertificate: {cert_path}")
    print(f"Private Key: {key_path}")
    print(f"Valid for: {validity_days} days")
    print(f"Common Name: {common_name}")
    print("\n⚠️  WARNING: This is a self-signed certificate for development only!")
    print("   Do NOT use in production. Use Let's Encrypt or a proper CA instead.")
    print("\n📝 To use with Uvicorn:")
    print(f"   uvicorn app.main:app --ssl-keyfile={key_path} --ssl-certfile={cert_path}")
    print("\n📝 To trust this certificate in your browser:")
    print("   - Chrome/Edge: Visit chrome://settings/certificates")
    print("   - Firefox: Visit about:preferences#privacy -> View Certificates")
    print("   - Import the certificate and trust it for identifying websites")
    print("="*60 + "\n")


def main():
    """Main function"""
    # Get backend directory (parent of scripts directory)
    backend_dir = Path(__file__).parent.parent
    certs_dir = backend_dir / "certs"
    
    try:
        generate_self_signed_cert(
            output_dir=certs_dir,
            cert_name="dev-cert.pem",
            key_name="dev-key.pem",
            common_name="localhost",
            validity_days=365
        )
        return 0
    except Exception as e:
        print(f"\n❌ Error generating certificate: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
