# TLS 1.3 Deployment Guide for Multilingual Mandi

This guide provides comprehensive instructions for deploying the Multilingual Mandi API with TLS 1.3 encryption.

**Requirements Addressed**: 15.1 - Encrypt all voice data during transmission using TLS 1.3 or higher

## Table of Contents

1. [Overview](#overview)
2. [Development Setup](#development-setup)
3. [Production Deployment](#production-deployment)
4. [Certificate Management](#certificate-management)
5. [Testing TLS Configuration](#testing-tls-configuration)
6. [Troubleshooting](#troubleshooting)
7. [Security Best Practices](#security-best-practices)

---

## Overview

The Multilingual Mandi API enforces TLS 1.3 for all connections to ensure:
- **Encryption**: All voice data and API communications are encrypted in transit
- **Authentication**: Server identity is verified using SSL certificates
- **Integrity**: Data cannot be tampered with during transmission
- **Forward Secrecy**: Past communications remain secure even if keys are compromised

### Architecture

```
Client (Browser/App)
    ↓ HTTPS (TLS 1.3)
Nginx Reverse Proxy
    ↓ HTTP (internal network)
FastAPI Backend (Uvicorn)
```

---

## Development Setup

For local development and testing, use self-signed certificates.

### Step 1: Install Dependencies

```bash
# Install cryptography library for certificate generation
pip install cryptography
```

### Step 2: Generate Self-Signed Certificates

```bash
# From the backend directory
python scripts/generate_dev_certs.py
```

This creates:
- `certs/dev-cert.pem` - SSL certificate
- `certs/dev-key.pem` - Private key

### Step 3: Run Uvicorn with TLS

```bash
# Option 1: Using command line
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8443 \
    --ssl-keyfile=certs/dev-key.pem \
    --ssl-certfile=certs/dev-cert.pem

# Option 2: Using Python script
python -c "
import uvicorn
from app.core.tls_config import get_uvicorn_ssl_config

ssl_config = get_uvicorn_ssl_config(
    cert_file='certs/dev-cert.pem',
    key_file='certs/dev-key.pem'
)

uvicorn.run(
    'app.main:app',
    host='0.0.0.0',
    port=8443,
    **ssl_config
)
"
```

### Step 4: Trust the Certificate (Optional)

To avoid browser warnings:

**Chrome/Edge**:
1. Visit `chrome://settings/certificates`
2. Go to "Authorities" tab
3. Click "Import" and select `certs/dev-cert.pem`
4. Check "Trust this certificate for identifying websites"

**Firefox**:
1. Visit `about:preferences#privacy`
2. Scroll to "Certificates" → "View Certificates"
3. Go to "Authorities" tab
4. Click "Import" and select `certs/dev-cert.pem`

**macOS**:
```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain certs/dev-cert.pem
```

**Linux**:
```bash
sudo cp certs/dev-cert.pem /usr/local/share/ca-certificates/multilingual-mandi-dev.crt
sudo update-ca-certificates
```

### Step 5: Test the Connection

```bash
# Test HTTPS endpoint
curl -k https://localhost:8443/health

# Verify TLS 1.3 is being used
openssl s_client -connect localhost:8443 -tls1_3
```

---

## Production Deployment

For production, use Let's Encrypt for free, trusted SSL certificates.

### Prerequisites

- Domain name (e.g., `api.multilingualmandi.in`)
- DNS A record pointing to your server's IP
- Ubuntu/Debian server with Docker and Docker Compose installed
- Ports 80 and 443 open in firewall

### Step 1: Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd multilingual-mandi/backend

# Create environment file
cp .env.example .env.prod
nano .env.prod
```

Edit `.env.prod`:
```env
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/multilingual_mandi
POSTGRES_USER=multilingual_mandi
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=multilingual_mandi

# Redis
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=<generate-strong-secret-key>
ALLOWED_ORIGINS=https://multilingualmandi.in,https://www.multilingualmandi.in

# Monitoring
GRAFANA_PASSWORD=<strong-password>
```

### Step 2: Obtain SSL Certificate

```bash
# Create directories
mkdir -p deployment/certbot/conf deployment/certbot/www

# Get initial certificate
docker-compose -f deployment/docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email admin@multilingualmandi.in \
    --agree-tos \
    --no-eff-email \
    -d api.multilingualmandi.in
```

### Step 3: Update Nginx Configuration

Edit `deployment/nginx/multilingual-mandi.conf` and replace `api.multilingualmandi.in` with your domain.

### Step 4: Start Services

```bash
# Start all services
docker-compose -f deployment/docker-compose.prod.yml up -d

# Check logs
docker-compose -f deployment/docker-compose.prod.yml logs -f

# Verify services are running
docker-compose -f deployment/docker-compose.prod.yml ps
```

### Step 5: Verify TLS Configuration

```bash
# Test HTTPS endpoint
curl https://api.multilingualmandi.in/health

# Verify TLS 1.3
openssl s_client -connect api.multilingualmandi.in:443 -tls1_3

# Check SSL Labs rating (should be A+)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=api.multilingualmandi.in
```

---

## Certificate Management

### Automatic Renewal

Let's Encrypt certificates expire after 90 days. The Certbot container automatically renews them.

To manually renew:
```bash
docker-compose -f deployment/docker-compose.prod.yml run --rm certbot renew
docker-compose -f deployment/docker-compose.prod.yml restart nginx
```

### Certificate Monitoring

Set up monitoring to alert before expiration:

```bash
# Check certificate expiration
openssl s_client -connect api.multilingualmandi.in:443 -servername api.multilingualmandi.in 2>/dev/null | \
    openssl x509 -noout -dates
```

### Backup Certificates

```bash
# Backup Let's Encrypt certificates
tar -czf letsencrypt-backup-$(date +%Y%m%d).tar.gz deployment/certbot/conf

# Store backup securely (e.g., encrypted cloud storage)
```

---

## Testing TLS Configuration

### 1. Verify TLS Version

```bash
# Test TLS 1.3 connection
openssl s_client -connect api.multilingualmandi.in:443 -tls1_3

# Should see: "Protocol  : TLSv1.3"
```

### 2. Test Cipher Suites

```bash
# List supported ciphers
nmap --script ssl-enum-ciphers -p 443 api.multilingualmandi.in

# Should only show TLS 1.3 ciphers:
# - TLS_AES_256_GCM_SHA384
# - TLS_AES_128_GCM_SHA256
# - TLS_CHACHA20_POLY1305_SHA256
```

### 3. Check Security Headers

```bash
# Verify HSTS and other security headers
curl -I https://api.multilingualmandi.in/health

# Should include:
# Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
```

### 4. SSL Labs Test

Visit [SSL Labs](https://www.ssllabs.com/ssltest/) and test your domain. You should get an **A+** rating.

### 5. Automated Testing

```bash
# Run TLS tests
cd backend
pytest tests/test_tls_config.py -v
```

---

## Troubleshooting

### Issue: Certificate Not Found

**Error**: `ssl.SSLError: [SSL] PEM lib (_ssl.c:4067)`

**Solution**:
```bash
# Verify certificate files exist
ls -la deployment/certbot/conf/live/api.multilingualmandi.in/

# Check file permissions
chmod 644 deployment/certbot/conf/live/api.multilingualmandi.in/fullchain.pem
chmod 600 deployment/certbot/conf/live/api.multilingualmandi.in/privkey.pem
```

### Issue: TLS 1.2 Still Accepted

**Error**: Server accepts TLS 1.2 connections

**Solution**:
```bash
# Check Nginx configuration
docker exec multilingual-mandi-nginx nginx -T | grep ssl_protocols

# Should show: ssl_protocols TLSv1.3;

# Reload Nginx
docker-compose -f deployment/docker-compose.prod.yml restart nginx
```

### Issue: Mixed Content Warnings

**Error**: Browser shows "Not Secure" despite HTTPS

**Solution**:
- Ensure all API calls use HTTPS URLs
- Check Content Security Policy headers
- Verify HSTS header is present

### Issue: Certificate Renewal Failed

**Error**: Certbot renewal fails

**Solution**:
```bash
# Check Certbot logs
docker-compose -f deployment/docker-compose.prod.yml logs certbot

# Manually renew with verbose output
docker-compose -f deployment/docker-compose.prod.yml run --rm certbot renew --dry-run -v

# Ensure port 80 is accessible for ACME challenge
curl http://api.multilingualmandi.in/.well-known/acme-challenge/test
```

---

## Security Best Practices

### 1. Keep Software Updated

```bash
# Update Docker images regularly
docker-compose -f deployment/docker-compose.prod.yml pull
docker-compose -f deployment/docker-compose.prod.yml up -d
```

### 2. Monitor TLS Connections

```bash
# Monitor TLS version usage
tail -f deployment/logs/nginx/multilingual-mandi-access.log | grep "TLS"

# Set up alerts for TLS 1.2 connections (should be none)
```

### 3. Implement Certificate Pinning (Optional)

For mobile apps, implement certificate pinning to prevent MITM attacks:

```python
# Example for Python requests library
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

class TLS13Adapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

session = requests.Session()
session.mount('https://', TLS13Adapter())
```

### 4. Regular Security Audits

```bash
# Run security scan
docker run --rm -it aquasec/trivy image multilingual-mandi-backend

# Check for vulnerabilities
npm audit  # For frontend
pip-audit  # For backend
```

### 5. Implement Rate Limiting

Add rate limiting to Nginx configuration:

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    # ... rest of configuration
}
```

### 6. Enable Fail2Ban

Protect against brute force attacks:

```bash
# Install Fail2Ban
sudo apt-get install fail2ban

# Configure for Nginx
sudo nano /etc/fail2ban/jail.local
```

Add:
```ini
[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/multilingual-mandi-error.log
maxretry = 5
bantime = 3600
```

---

## Compliance Checklist

- [x] TLS 1.3 enforced for all connections
- [x] TLS 1.0, 1.1, 1.2 disabled
- [x] Strong cipher suites configured
- [x] HSTS header enabled with preload
- [x] Security headers configured (CSP, X-Frame-Options, etc.)
- [x] Certificate auto-renewal configured
- [x] Certificate monitoring in place
- [x] Forward secrecy enabled
- [x] OCSP stapling enabled
- [x] HTTP to HTTPS redirect configured

---

## Additional Resources

- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)
- [Nginx TLS Best Practices](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [SSL Labs Best Practices](https://github.com/ssllabs/research/wiki/SSL-and-TLS-Deployment-Best-Practices)

---

## Support

For issues or questions:
- Check logs: `docker-compose -f deployment/docker-compose.prod.yml logs`
- Review Nginx config: `docker exec multilingual-mandi-nginx nginx -T`
- Test TLS: `openssl s_client -connect api.multilingualmandi.in:443 -tls1_3`

**Security Issues**: Report to security@multilingualmandi.in
