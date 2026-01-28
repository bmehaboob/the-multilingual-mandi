# Production Deployment Guide - Multilingual Mandi

**Version:** 1.0.0  
**Last Updated:** January 28, 2026  
**Status:** Production Ready (with Python version fix)

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Backend Deployment](#backend-deployment)
4. [Frontend Deployment](#frontend-deployment)
5. [Database Setup](#database-setup)
6. [Monitoring Setup](#monitoring-setup)
7. [Security Configuration](#security-configuration)
8. [Performance Optimization](#performance-optimization)
9. [Post-Deployment Verification](#post-deployment-verification)
10. [Rollback Procedures](#rollback-procedures)

---

## Pre-Deployment Checklist

### Critical Requirements
- [ ] **Python Version**: Downgrade backend to Python 3.11 or 3.12 (NOT 3.13)
- [ ] **SSL Certificates**: Obtain valid SSL certificates for production domain
- [ ] **Environment Variables**: Configure all production environment variables
- [ ] **Database**: Set up production PostgreSQL database
- [ ] **Redis**: Set up production Redis instance
- [ ] **Domain**: Configure DNS records for production domain
- [ ] **Backup Strategy**: Implement database backup procedures

### Optional but Recommended
- [ ] **eNAM API Access**: Obtain official API credentials (fallback to demo data)
- [ ] **CDN**: Configure CDN for static assets
- [ ] **Load Balancer**: Set up external load balancer (AWS ELB, etc.)
- [ ] **Monitoring**: Configure external monitoring (Datadog, New Relic, etc.)

---

## Environment Setup

### 1. Python Version Fix (CRITICAL)

**Issue**: SQLAlchemy 2.0.46 is incompatible with Python 3.13.7

**Solution**:
```bash
# Install Python 3.11 or 3.12
# On Windows with pyenv:
pyenv install 3.11.7
pyenv local 3.11.7

# On Linux/Mac:
sudo apt-get install python3.11
# or
brew install python@3.11

# Verify version
python --version  # Should show 3.11.x or 3.12.x
```

### 2. Install Dependencies

**Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend**:
```bash
cd frontend
npm install
```

---

## Backend Deployment

### 1. Environment Configuration

Create `backend/.env.production`:
```env
# Database
DATABASE_URL=postgresql://user:password@prod-db-host:5432/multilingual_mandi
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://prod-redis-host:6379/0
REDIS_PASSWORD=your_redis_password

# Security
SECRET_KEY=your_super_secret_key_min_32_chars
JWT_SECRET_KEY=your_jwt_secret_key_min_32_chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# TLS/SSL
TLS_ENABLED=true
TLS_CERT_PATH=/path/to/cert.pem
TLS_KEY_PATH=/path/to/key.pem

# API Configuration
API_V1_PREFIX=/api/v1
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# AI/ML Models
MODEL_CACHE_DIR=/var/cache/multilingual-mandi/models
ENABLE_MODEL_QUANTIZATION=true

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 2. Database Migrations

```bash
cd backend
source venv/bin/activate

# Run migrations
alembic upgrade head

# Verify migrations
alembic current
```

### 3. Build and Deploy

**Using Docker**:
```bash
cd backend
docker build -t multilingual-mandi-backend:1.0.0 .
docker push your-registry/multilingual-mandi-backend:1.0.0
```

**Using systemd** (Linux):
```bash
# Create systemd service file
sudo nano /etc/systemd/system/multilingual-mandi.service
```

```ini
[Unit]
Description=Multilingual Mandi Backend
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/multilingual-mandi/backend
Environment="PATH=/var/www/multilingual-mandi/backend/venv/bin"
ExecStart=/var/www/multilingual-mandi/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable multilingual-mandi
sudo systemctl start multilingual-mandi
```

### 4. Nginx Configuration

```nginx
# /etc/nginx/sites-available/multilingual-mandi
upstream backend {
    least_conn;
    server 127.0.0.1:8000 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 weight=1 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    ssl_protocols TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://backend/health;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Frontend Deployment

### 1. Environment Configuration

Create `frontend/.env.production`:
```env
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1
VITE_WS_URL=wss://api.yourdomain.com/ws
VITE_ENABLE_ANALYTICS=true
VITE_SENTRY_DSN=your_sentry_dsn
VITE_APP_VERSION=1.0.0
```

### 2. Build for Production

```bash
cd frontend
npm run build

# Verify build
ls -lh dist/
# Should show optimized bundle < 500 KB
```

### 3. Deploy Static Files

**Option A: Nginx**:
```nginx
# /etc/nginx/sites-available/multilingual-mandi-frontend
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    ssl_protocols TLSv1.3;

    root /var/www/multilingual-mandi/frontend/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Service worker - no cache
    location /sw.js {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        expires 0;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**Option B: CDN (Cloudflare, AWS CloudFront)**:
```bash
# Upload to S3
aws s3 sync dist/ s3://your-bucket-name/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

---

## Database Setup

### 1. PostgreSQL Configuration

```sql
-- Create production database
CREATE DATABASE multilingual_mandi;

-- Create user
CREATE USER mandi_user WITH ENCRYPTED PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE multilingual_mandi TO mandi_user;

-- Enable extensions
\c multilingual_mandi
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
```

### 2. Connection Pooling

Use PgBouncer for connection pooling:
```ini
# /etc/pgbouncer/pgbouncer.ini
[databases]
multilingual_mandi = host=localhost port=5432 dbname=multilingual_mandi

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

### 3. Backup Strategy

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR=/var/backups/multilingual-mandi
DATE=$(date +%Y%m%d_%H%M%S)

pg_dump -U mandi_user multilingual_mandi | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

---

## Monitoring Setup

### 1. Prometheus + Grafana

```bash
cd backend/monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. Configure Alerts

Edit `backend/monitoring/prometheus/rules/latency_alerts.yml`:
```yaml
groups:
  - name: latency_alerts
    rules:
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency detected"
          description: "95th percentile latency is {{ $value }}s"

      - alert: VoicePipelineLatency
        expr: voice_pipeline_latency_seconds > 8
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Voice pipeline latency exceeded"
          description: "Voice pipeline latency is {{ $value }}s (threshold: 8s)"
```

### 3. Health Checks

```bash
# Add to cron
*/5 * * * * curl -f https://api.yourdomain.com/health || echo "API health check failed" | mail -s "Alert" admin@yourdomain.com
```

---

## Security Configuration

### 1. Firewall Rules

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH
sudo ufw enable

# Deny direct access to backend ports
sudo ufw deny 8000/tcp
sudo ufw deny 8001/tcp
sudo ufw deny 8002/tcp
```

### 2. SSL/TLS Certificates

**Using Let's Encrypt**:
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com
```

### 3. Security Headers

Already configured in Nginx (see above), but verify:
```bash
curl -I https://yourdomain.com | grep -i "strict-transport-security\|x-frame-options\|x-content-type-options"
```

---

## Performance Optimization

### 1. Database Indexing

```sql
-- Add indexes for common queries
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_transactions_user ON transactions(buyer_id, seller_id);
CREATE INDEX idx_price_data_commodity ON price_data(commodity, timestamp DESC);
```

### 2. Redis Caching

```bash
# Configure Redis for production
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET save "900 1 300 10 60 10000"
```

### 3. Auto-Scaling

```bash
# Start autoscaler
cd backend/deployment/autoscaling
python autoscaler.py --config production.yaml
```

---

## Post-Deployment Verification

### 1. Run Test Suite

```bash
# Frontend tests
cd frontend
npm test

# Backend tests (after Python version fix)
cd backend
pytest tests/ -v
```

### 2. Smoke Tests

```bash
# API health check
curl https://api.yourdomain.com/health

# Frontend accessibility
curl -I https://yourdomain.com

# WebSocket connection
wscat -c wss://api.yourdomain.com/ws

# Price query test
curl -X POST https://api.yourdomain.com/api/v1/prices/query \
  -H "Content-Type: application/json" \
  -d '{"commodity": "tomato", "location": {"state": "Maharashtra"}}'
```

### 3. Performance Tests

```bash
# Load testing with Apache Bench
ab -n 1000 -c 10 https://api.yourdomain.com/health

# Expected: < 3s average response time
```

### 4. Security Scan

```bash
# SSL/TLS test
nmap --script ssl-enum-ciphers -p 443 yourdomain.com

# OWASP ZAP scan
zap-cli quick-scan https://yourdomain.com
```

---

## Rollback Procedures

### 1. Backend Rollback

```bash
# Stop current version
sudo systemctl stop multilingual-mandi

# Restore previous version
docker pull your-registry/multilingual-mandi-backend:0.9.0
docker run -d --name backend your-registry/multilingual-mandi-backend:0.9.0

# Rollback database if needed
psql -U mandi_user multilingual_mandi < /var/backups/multilingual-mandi/db_20260127.sql
```

### 2. Frontend Rollback

```bash
# Restore previous build
cd /var/www/multilingual-mandi/frontend
rm -rf dist
tar -xzf backups/dist-20260127.tar.gz

# Or rollback CDN
aws s3 sync s3://your-bucket-name-backup/ s3://your-bucket-name/ --delete
```

---

## Troubleshooting

### Common Issues

**1. Python 3.13 Compatibility Error**
```
Error: AssertionError: Class <class 'sqlalchemy.sql.elements.SQLCoreOperations'>...
```
**Solution**: Downgrade to Python 3.11 or 3.12

**2. High Memory Usage**
```bash
# Check memory
free -h

# Restart services
sudo systemctl restart multilingual-mandi
sudo systemctl restart redis
```

**3. Database Connection Pool Exhausted**
```bash
# Check connections
psql -U mandi_user -c "SELECT count(*) FROM pg_stat_activity;"

# Increase pool size in .env
DATABASE_POOL_SIZE=30
DATABASE_MAX_OVERFLOW=20
```

---

## Maintenance Schedule

### Daily
- Monitor error logs
- Check disk space
- Verify backup completion

### Weekly
- Review performance metrics
- Update SSL certificates if needed
- Clean up old logs

### Monthly
- Security updates
- Database vacuum and analyze
- Review and optimize slow queries

---

## Support Contacts

- **Technical Lead**: [Your Name]
- **DevOps**: [DevOps Team]
- **On-Call**: [On-Call Number]
- **Emergency**: [Emergency Contact]

---

## Appendix

### A. Environment Variables Reference

See `backend/.env.example` and `frontend/.env.example` for complete list.

### B. API Documentation

Available at: `https://api.yourdomain.com/docs`

### C. Monitoring Dashboards

- Grafana: `http://monitoring.yourdomain.com:3000`
- Prometheus: `http://monitoring.yourdomain.com:9090`

---

**Document Version**: 1.0.0  
**Last Review**: January 28, 2026  
**Next Review**: February 28, 2026
