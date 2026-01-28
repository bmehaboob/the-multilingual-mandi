# Load Balancing Guide for Multilingual Mandi

## Overview

This guide explains the load balancing configuration for the Multilingual Mandi platform. The system uses Nginx as a reverse proxy and load balancer to distribute traffic across multiple backend instances, ensuring high availability and scalability.

**Requirements Addressed:**
- Requirement 24.5: Load balancing across multiple servers for high availability
- Requirement 24.1: Support at least 10,000 concurrent users
- Requirement 24.4: Maintain average response times under 3 seconds for 99% of requests

## Architecture

```
                                    ┌─────────────────┐
                                    │   Client        │
                                    │   (Browser/PWA) │
                                    └────────┬────────┘
                                             │
                                             │ HTTPS/TLS 1.3
                                             │
                                    ┌────────▼────────┐
                                    │  Nginx Reverse  │
                                    │  Proxy + LB     │
                                    └────────┬────────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        │                    │                    │
                   ┌────▼─────┐       ┌─────▼────┐       ┌──────▼────┐
                   │ Backend  │       │ Backend  │       │ Backend   │
                   │ Instance │       │ Instance │       │ Instance  │
                   │    #1    │       │    #2    │       │    #3     │
                   └────┬─────┘       └─────┬────┘       └──────┬────┘
                        │                   │                    │
                        └───────────────────┼────────────────────┘
                                            │
                        ┌───────────────────┼────────────────────┐
                        │                   │                    │
                   ┌────▼─────┐       ┌────▼─────┐       ┌──────▼────┐
                   │PostgreSQL│       │  Redis   │       │Prometheus │
                   │ Database │       │  Cache   │       │ Metrics   │
                   └──────────┘       └──────────┘       └───────────┘
```

## Load Balancing Strategy

### Algorithm: Least Connections

The system uses the **least connections** algorithm, which routes requests to the backend server with the fewest active connections. This is optimal for the Multilingual Mandi platform because:

1. **Voice Processing Workloads**: Voice-to-voice translation involves long-running requests (up to 8 seconds per request)
2. **Variable Request Duration**: Different requests have different processing times (STT, translation, TTS)
3. **Fair Distribution**: Ensures no single server becomes overloaded while others are idle

### Alternative Strategies

The configuration includes several alternative load balancing strategies in `load-balancing.conf`:

- **IP Hash**: Maintains session persistence by routing the same client to the same backend
- **Round Robin with Weights**: Distributes requests evenly with weighted distribution
- **Backup Servers**: Designates backup servers that only receive traffic when primary servers fail

## Configuration Files

### 1. Main Nginx Configuration

**File**: `backend/deployment/nginx/multilingual-mandi.conf`

Key features:
- TLS 1.3 enforcement for all connections
- Upstream backend configuration with health checks
- WebSocket support for real-time audio streaming
- Security headers (HSTS, CSP, etc.)
- Request size limits (10MB for audio uploads)
- Timeout configurations

### 2. Advanced Load Balancing Configuration

**File**: `backend/deployment/nginx/load-balancing.conf`

Includes:
- Multiple load balancing strategies
- Geographic/zone-based routing
- Service-specific upstream groups
- Health check configurations
- Best practices and examples

### 3. Docker Compose Configuration

**File**: `backend/deployment/docker-compose.prod.yml`

Defines:
- Three backend instances (backend, backend-2, backend-3)
- Nginx reverse proxy
- PostgreSQL database
- Redis cache
- Prometheus and Grafana for monitoring

## Backend Instance Configuration

### Instance Parameters

Each backend instance is configured with:

```nginx
server backend:8000 max_fails=3 fail_timeout=30s weight=1;
```

- **max_fails**: Number of failed health checks before marking server as down (3)
- **fail_timeout**: Time to wait before retrying a failed server (30 seconds)
- **weight**: Relative weight for load distribution (1 = equal distribution)

### Health Checks

Health checks are performed via the `/health` endpoint:

```nginx
location /health {
    proxy_pass http://multilingual_mandi_backend;
    access_log off;
    proxy_connect_timeout 5s;
    proxy_read_timeout 5s;
    proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
}
```

If a backend fails 3 consecutive health checks, it's marked as down and removed from rotation for 30 seconds.

## Deployment

### Starting the Load Balanced System

1. **Navigate to deployment directory**:
   ```bash
   cd backend/deployment
   ```

2. **Set environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Verify all backends are running**:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

5. **Check health status**:
   ```bash
   chmod +x scripts/health_check.sh
   ./scripts/health_check.sh check
   ```

### Scaling Backend Instances

#### Adding More Instances

1. **Update docker-compose.prod.yml**:
   ```yaml
   backend-4:
     build:
       context: ..
       dockerfile: deployment/Dockerfile
     container_name: multilingual-mandi-backend-4
     restart: unless-stopped
     environment:
       - DATABASE_URL=${DATABASE_URL}
       - REDIS_URL=redis://redis:6379/0
       - SECRET_KEY=${SECRET_KEY}
       - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
       - DEBUG=false
       - INSTANCE_ID=backend-4
     volumes:
       - ../models:/app/models:ro
     depends_on:
       - postgres
       - redis
     networks:
       - multilingual-mandi-network
     healthcheck:
       test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
       interval: 30s
       timeout: 10s
       retries: 3
       start_period: 40s
   ```

2. **Update Nginx upstream configuration**:
   ```nginx
   upstream multilingual_mandi_backend {
       least_conn;
       server backend:8000 max_fails=3 fail_timeout=30s weight=1;
       server backend-2:8000 max_fails=3 fail_timeout=30s weight=1;
       server backend-3:8000 max_fails=3 fail_timeout=30s weight=1;
       server backend-4:8000 max_fails=3 fail_timeout=30s weight=1;
       keepalive 64;
   }
   ```

3. **Reload Nginx configuration**:
   ```bash
   docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
   ```

4. **Start the new instance**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d backend-4
   ```

#### Removing Instances

1. **Mark server as down in Nginx config** (graceful removal):
   ```nginx
   server backend-3:8000 down;
   ```

2. **Reload Nginx**:
   ```bash
   docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
   ```

3. **Wait for existing connections to complete** (check logs)

4. **Stop the instance**:
   ```bash
   docker-compose -f docker-compose.prod.yml stop backend-3
   ```

5. **Remove from configuration** and reload

## Monitoring

### Health Check Script

The `health_check.sh` script provides several monitoring capabilities:

```bash
# Check health once
./scripts/health_check.sh check

# Continuous monitoring (every 30 seconds)
./scripts/health_check.sh monitor 30

# Get detailed health information
./scripts/health_check.sh detailed

# Check load distribution
./scripts/health_check.sh load

# Test failover behavior
./scripts/health_check.sh failover backend:8000
```

### Nginx Status

Enable the stub_status module for basic metrics:

```nginx
location /nginx_status {
    stub_status;
    allow 127.0.0.1;
    deny all;
}
```

Access metrics:
```bash
curl http://localhost/nginx_status
```

### Prometheus Metrics

The system includes Prometheus for comprehensive metrics collection:

- **Endpoint**: http://localhost:9090
- **Metrics**: Request rates, latencies, error rates, backend health
- **Dashboards**: Grafana dashboards at http://localhost:3000

### Log Analysis

Monitor Nginx access logs for load distribution:

```bash
# View access logs
docker-compose -f docker-compose.prod.yml logs -f nginx

# Analyze backend distribution
docker-compose -f docker-compose.prod.yml logs nginx | grep "upstream:" | awk '{print $NF}' | sort | uniq -c
```

## Performance Tuning

### Connection Pooling

The configuration uses connection pooling to reduce latency:

```nginx
keepalive 64;              # Number of idle keepalive connections
keepalive_requests 100;    # Max requests per connection
keepalive_timeout 60s;     # Timeout for idle connections
```

### Timeouts

Configured for voice processing workloads:

```nginx
proxy_connect_timeout 60s;  # Time to establish connection
proxy_send_timeout 60s;     # Time to send request to backend
proxy_read_timeout 60s;     # Time to read response from backend
```

### Buffer Sizes

Optimized for audio data:

```nginx
client_max_body_size 10M;      # Max request size (audio uploads)
client_body_buffer_size 128k;  # Buffer for request body
proxy_buffering off;           # Disable buffering for streaming
```

### Worker Configuration

In main `nginx.conf`:

```nginx
worker_processes auto;           # One worker per CPU core
worker_connections 1024;         # Max connections per worker
worker_rlimit_nofile 2048;      # Max open files
```

## Failover and High Availability

### Automatic Failover

When a backend fails:

1. Nginx detects failure via health check or request error
2. Request is automatically retried on another backend
3. Failed backend is marked as down for `fail_timeout` period
4. After timeout, backend is retried with a single request
5. If successful, backend is restored to rotation

### Failover Configuration

```nginx
proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
proxy_next_upstream_tries 3;      # Max retry attempts
proxy_next_upstream_timeout 10s;  # Max time for retries
```

### Testing Failover

1. **Simulate backend failure**:
   ```bash
   docker-compose -f docker-compose.prod.yml stop backend-2
   ```

2. **Make test requests**:
   ```bash
   for i in {1..10}; do
     curl -s https://api.multilingualmandi.in/health
   done
   ```

3. **Verify requests are handled by other backends** (check logs)

4. **Restore backend**:
   ```bash
   docker-compose -f docker-compose.prod.yml start backend-2
   ```

5. **Verify backend rejoins rotation**

## Security Considerations

### Backend Isolation

- Backend instances are not directly accessible from the internet
- All traffic goes through Nginx reverse proxy
- Internal network isolation via Docker networks

### TLS Termination

- TLS 1.3 is terminated at Nginx
- Backend communication uses HTTP (within secure Docker network)
- For additional security, enable TLS between Nginx and backends

### Rate Limiting

Implement rate limiting to prevent abuse:

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location / {
    limit_req zone=api_limit burst=20 nodelay;
    proxy_pass http://multilingual_mandi_backend;
}
```

### DDoS Protection

- Connection limits per IP
- Request rate limiting
- Timeout configurations
- Fail2ban integration (optional)

## Troubleshooting

### All Backends Showing as Down

1. **Check backend health**:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   docker-compose -f docker-compose.prod.yml logs backend
   ```

2. **Verify network connectivity**:
   ```bash
   docker-compose -f docker-compose.prod.yml exec nginx ping backend
   ```

3. **Check health endpoint**:
   ```bash
   docker-compose -f docker-compose.prod.yml exec nginx curl http://backend:8000/health
   ```

### Uneven Load Distribution

1. **Check active connections**:
   ```bash
   docker-compose -f docker-compose.prod.yml logs nginx | grep "upstream"
   ```

2. **Verify backend performance**:
   ```bash
   ./scripts/health_check.sh load
   ```

3. **Consider adjusting weights**:
   ```nginx
   server backend:8000 weight=2;    # Receives 2x traffic
   server backend-2:8000 weight=1;  # Receives 1x traffic
   ```

### High Latency

1. **Check backend response times**:
   ```bash
   docker-compose -f docker-compose.prod.yml logs backend | grep "latency"
   ```

2. **Monitor Prometheus metrics**:
   - Request duration histograms
   - Backend processing times
   - Queue depths

3. **Scale horizontally**:
   - Add more backend instances
   - Increase worker processes

### Connection Errors

1. **Check keepalive settings**:
   ```nginx
   keepalive 64;  # Increase if needed
   ```

2. **Verify timeout configurations**:
   ```nginx
   proxy_connect_timeout 60s;  # Increase if needed
   ```

3. **Check system limits**:
   ```bash
   ulimit -n  # Max open files
   ```

## Best Practices

### 1. Gradual Scaling

- Add instances one at a time
- Monitor performance after each addition
- Verify even load distribution

### 2. Health Check Tuning

- Adjust `max_fails` based on failure patterns
- Set `fail_timeout` to balance recovery speed and stability
- Monitor false positives (healthy backends marked as down)

### 3. Capacity Planning

- Monitor resource utilization (CPU, memory, network)
- Scale before reaching 80% capacity (Requirement 24.3)
- Plan for peak traffic (festivals, market hours)

### 4. Maintenance Windows

- Use `down` parameter for graceful removal
- Drain connections before stopping instances
- Update instances one at a time (rolling updates)

### 5. Monitoring and Alerting

- Set up alerts for backend failures
- Monitor response times and error rates
- Track load distribution metrics
- Review logs regularly

## Performance Benchmarks

### Expected Performance

With 3 backend instances:

- **Concurrent Users**: 10,000+ (Requirement 24.1)
- **Response Time**: < 3 seconds for 99% of requests (Requirement 24.4)
- **Voice Translation Latency**: < 8 seconds end-to-end (Requirement 5.1)
- **Throughput**: 100+ requests/second per instance

### Load Testing

Use tools like Apache Bench or Locust:

```bash
# Apache Bench
ab -n 10000 -c 100 https://api.multilingualmandi.in/health

# Locust (Python)
locust -f load_test.py --host=https://api.multilingualmandi.in
```

## References

- [Nginx Load Balancing Documentation](https://nginx.org/en/docs/http/load_balancing.html)
- [Nginx Upstream Module](https://nginx.org/en/docs/http/ngx_http_upstream_module.html)
- [Docker Compose Networking](https://docs.docker.com/compose/networking/)
- Multilingual Mandi Design Document: Section on Architecture and Scalability

## Support

For issues or questions:
1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Run health checks: `./scripts/health_check.sh check`
3. Review Prometheus metrics: http://localhost:9090
4. Consult this guide and Nginx documentation
