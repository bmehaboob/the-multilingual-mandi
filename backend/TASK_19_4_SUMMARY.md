# Task 19.4 Summary: Set up Prometheus and Grafana

**Status**: ✅ Complete

**Requirements**: 18.4, 24.7

## Overview

Implemented a comprehensive monitoring stack using Prometheus and Grafana for the Multilingual Mandi platform. The setup includes metrics collection, alerting for latency thresholds (>10s), and visualization dashboards.

## What Was Implemented

### 1. Prometheus Configuration

**File**: `backend/monitoring/prometheus/prometheus.yml`

- Configured scrape targets for:
  - FastAPI application (`/metrics` endpoint)
  - PostgreSQL (via postgres_exporter)
  - Redis (via redis_exporter)
  - System metrics (via node_exporter)
  - Nginx (via nginx-exporter)
- Set scrape interval to 15 seconds
- Configured Alertmanager integration
- Loaded alert rules from `rules/` directory

### 2. Alert Rules

**File**: `backend/monitoring/prometheus/rules/latency_alerts.yml`

Implemented three alert groups:

#### Latency Alerts (Requirement 18.4)
- **VoicePipelineHighLatency**: Fires when voice pipeline latency exceeds 10 seconds
- **STTServiceHighLatency**: Fires when STT latency exceeds 3 seconds
- **TranslationServiceHighLatency**: Fires when translation latency exceeds 2 seconds
- **TTSServiceHighLatency**: Fires when TTS latency exceeds 2 seconds
- **APIHighResponseTime**: Fires when API p99 latency exceeds 3 seconds
- **PriceQueryHighLatency**: Fires when price query latency exceeds 3 seconds

#### System Health Alerts
- **HighErrorRate**: Fires when error rate exceeds 5%
- **ServiceDown**: Fires when a service is unreachable
- **HighCPUUsage**: Fires when CPU usage exceeds 80%
- **HighMemoryUsage**: Fires when memory usage exceeds 85%
- **DatabaseConnectionPoolExhausted**: Fires when DB pool usage exceeds 90%

#### Accuracy Alerts
- **HighSTTCorrectionRate**: Fires when STT correction rate exceeds 20%
- **HighTransactionAbandonmentRate**: Fires when abandonment rate exceeds 30%
- **LowTranslationConfidence**: Fires when average translation confidence drops below 0.85

### 3. Alertmanager Configuration

**File**: `backend/monitoring/alertmanager/alertmanager.yml`

- Configured alert routing by severity and component
- Set up multiple receivers:
  - `critical-alerts`: For critical issues (email + webhook)
  - `latency-alerts`: For performance team
  - `system-alerts`: For infrastructure team
  - `quality-alerts`: For ML/data team
- Implemented inhibition rules to prevent alert fatigue
- Configured webhook integration with FastAPI backend

### 4. Grafana Dashboards

#### System Overview Dashboard
**File**: `backend/monitoring/grafana/dashboards/multilingual-mandi-overview.json`

Panels include:
- Voice pipeline end-to-end latency (p50, p95, p99)
- Request rate by endpoint
- STT, Translation, and TTS service latencies
- Error rates (4xx and 5xx)
- STT correction rate by language
- Transaction completion rate
- Active users count
- System CPU and memory usage

#### Latency Monitoring Dashboard
**File**: `backend/monitoring/grafana/dashboards/latency-monitoring.json`

Panels include:
- Voice pipeline latency breakdown by stage
- Latency percentiles (p50, p75, p90, p95, p99)
- Latency by language pair
- Price query latency
- API endpoint latency
- Latency alerts table
- 24-hour latency trends

### 5. Prometheus Metrics Middleware

**File**: `backend/app/middleware/prometheus_metrics.py`

Implemented comprehensive metrics collection:

#### HTTP Metrics
- `http_requests_total`: Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds`: HTTP request latency histogram

#### Voice Pipeline Metrics (Requirement 18.1)
- `voice_pipeline_latency_seconds`: End-to-end latency
- `language_detection_latency_seconds`: Language detection latency
- `stt_latency_seconds`: STT latency by language
- `translation_latency_seconds`: Translation latency by language pair
- `tts_latency_seconds`: TTS latency by language

#### STT Accuracy Metrics (Requirement 18.2)
- `stt_correction_rate`: Correction rate by language
- `stt_confidence_score`: Confidence score distribution

#### Transaction Metrics (Requirement 18.3)
- `transaction_completion_rate`: Completion rate gauge
- `transaction_abandonment_rate`: Abandonment rate gauge
- `transaction_duration_seconds`: Duration histogram

#### System Metrics (Requirement 24.7)
- `active_users_total`: Active users count
- `active_conversations_total`: Active conversations count
- `db_connection_pool_usage`: Database pool usage
- `error_count_total`: Error counts by type and component

#### Helper Functions
- `record_voice_pipeline_latency()`: Record voice pipeline metrics
- `record_price_query_latency()`: Record price query metrics
- `update_stt_correction_rate()`: Update STT correction rate
- `record_stt_confidence()`: Record STT confidence scores
- `record_translation_confidence()`: Record translation confidence
- `update_transaction_rates()`: Update transaction rates
- `record_error()`: Record error occurrences

### 6. Docker Compose Configuration

**File**: `backend/monitoring/docker-compose.monitoring.yml`

Services included:
- **Prometheus**: Metrics collection and storage (port 9090)
- **Alertmanager**: Alert routing and management (port 9093)
- **Grafana**: Visualization and dashboards (port 3000)
- **Node Exporter**: System metrics (port 9100)
- **PostgreSQL Exporter**: Database metrics (port 9187)
- **Redis Exporter**: Cache metrics (port 9121)

Configuration:
- 30-day data retention for Prometheus
- Persistent volumes for all services
- Automatic restart policy
- Network isolation with backend network

### 7. Setup and Testing Scripts

#### Setup Script
**File**: `backend/monitoring/scripts/setup_monitoring.sh`

Features:
- Validates configuration files
- Starts monitoring stack with Docker Compose
- Checks service health
- Provides access URLs and next steps

#### Test Script
**File**: `backend/monitoring/scripts/test_monitoring.py`

Tests:
- Prometheus health and targets
- Alert rules loading
- Alertmanager health and configuration
- Grafana health, datasources, and dashboards
- Comprehensive test reporting

### 8. Documentation

**File**: `backend/monitoring/README.md`

Comprehensive documentation including:
- Quick start guide
- Architecture diagram
- Metrics reference
- Alert descriptions
- Configuration instructions
- Integration guide for FastAPI
- Monitoring best practices
- Troubleshooting guide
- Production deployment considerations
- Maintenance procedures

## Metrics Collected

### Voice Pipeline (Requirement 18.1)
- End-to-end latency with percentiles (p50, p95, p99)
- Per-stage latency (language detection, STT, translation, TTS)
- Latency by language pair

### STT Accuracy (Requirement 18.2)
- Correction rate by language
- Confidence score distribution
- Total transcriptions and corrections

### Transactions (Requirement 18.3)
- Completion rate
- Abandonment rate
- Duration distribution

### System Health (Requirement 24.7)
- Request rates and latencies
- Error rates by type
- CPU and memory usage
- Database connection pool usage
- Active users and conversations

## Alert Configuration (Requirement 18.4)

### Critical Alerts
- Voice pipeline latency > 10 seconds
- Service down
- High error rate (>5%)
- Database connection pool exhausted (>90%)

### Warning Alerts
- STT latency > 3 seconds
- Translation latency > 2 seconds
- TTS latency > 2 seconds
- API p99 latency > 3 seconds
- High STT correction rate (>20%)
- High transaction abandonment (>30%)
- High CPU usage (>80%)
- High memory usage (>85%)

## Integration with FastAPI

To integrate with the FastAPI application:

```python
from app.middleware.prometheus_metrics import PrometheusMiddleware, metrics_endpoint

# Add middleware
app.add_middleware(PrometheusMiddleware)

# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    return metrics_endpoint()
```

Record custom metrics:

```python
from app.middleware.prometheus_metrics import record_voice_pipeline_latency

record_voice_pipeline_latency(
    total_latency=7.5,
    source_language="hi",
    target_language="te",
    stt_latency=2.8,
    translation_latency=1.5,
    tts_latency=1.8
)
```

## Usage

### Start Monitoring Stack

```bash
cd backend/monitoring
./scripts/setup_monitoring.sh
```

Or manually:

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

### Access Services

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### Test Setup

```bash
cd backend/monitoring
python scripts/test_monitoring.py
```

### View Logs

```bash
docker-compose -f docker-compose.monitoring.yml logs -f
```

### Stop Monitoring Stack

```bash
docker-compose -f docker-compose.monitoring.yml down
```

## Files Created

```
backend/monitoring/
├── prometheus/
│   ├── prometheus.yml                    # Prometheus configuration
│   └── rules/
│       └── latency_alerts.yml           # Alert rules
├── alertmanager/
│   └── alertmanager.yml                 # Alertmanager configuration
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yml           # Datasource configuration
│   │   └── dashboards/
│   │       └── dashboards.yml           # Dashboard provisioning
│   └── dashboards/
│       ├── multilingual-mandi-overview.json    # Overview dashboard
│       └── latency-monitoring.json             # Latency dashboard
├── scripts/
│   ├── setup_monitoring.sh              # Setup script
│   └── test_monitoring.py               # Test script
├── docker-compose.monitoring.yml        # Docker Compose file
└── README.md                            # Documentation

backend/app/middleware/
└── prometheus_metrics.py                # Prometheus metrics middleware

backend/
└── TASK_19_4_SUMMARY.md                # This file
```

## Requirements Validation

### Requirement 18.4: System Latency Alerts
✅ **Satisfied**
- Implemented alerts for latency thresholds exceeding 10 seconds
- Voice pipeline latency alert fires when p99 latency > 10s
- Additional alerts for individual service latencies (STT, Translation, TTS)
- Alertmanager routes alerts to appropriate teams
- Webhook integration for programmatic alert handling

### Requirement 24.7: Resource Utilization Monitoring
✅ **Satisfied**
- Prometheus collects system metrics (CPU, memory, disk)
- Node Exporter provides detailed system metrics
- Grafana dashboards visualize resource utilization
- Alerts fire when resource thresholds are exceeded
- Database and Redis metrics tracked via exporters

## Testing

The monitoring setup can be tested using:

1. **Automated Tests**: Run `python scripts/test_monitoring.py`
   - Tests Prometheus health and configuration
   - Tests Alertmanager health and configuration
   - Tests Grafana health, datasources, and dashboards

2. **Manual Verification**:
   - Access Grafana dashboards
   - Check Prometheus targets at http://localhost:9090/targets
   - Verify alert rules at http://localhost:9090/alerts
   - Check Alertmanager at http://localhost:9093

3. **Integration Testing**:
   - Add middleware to FastAPI app
   - Generate test traffic
   - Verify metrics appear in Prometheus
   - Verify dashboards update in Grafana

## Production Considerations

### Security
- Change default Grafana password
- Configure Alertmanager SMTP credentials
- Enable authentication for Prometheus/Alertmanager
- Use TLS for external access
- Restrict network access to monitoring services

### Scaling
- Adjust Prometheus retention period based on storage
- Consider remote storage for long-term retention
- Use recording rules for expensive queries
- Implement high availability with multiple instances

### Maintenance
- Regular review of alerts and thresholds
- Update dashboards as features are added
- Monitor Prometheus storage usage
- Backup configurations and dashboards

## Next Steps

1. **Integration**: Add Prometheus middleware to FastAPI application
2. **Configuration**: Update Alertmanager with actual email/Slack credentials
3. **Customization**: Adjust alert thresholds based on actual performance
4. **Expansion**: Add more dashboards for specific features
5. **Testing**: Generate test traffic to verify metrics collection
6. **Documentation**: Train team on using Grafana dashboards

## Notes

- All alert thresholds are based on requirements specifications
- Dashboards are provisioned automatically on Grafana startup
- Metrics are retained for 30 days by default
- Alert rules can be modified without restarting Prometheus (use reload API)
- Grafana dashboards can be edited in the UI and exported

## References

- Requirements 18.4: Platform SHALL alert administrators when system latency exceeds 10 seconds
- Requirements 24.7: Platform SHALL monitor resource utilization and generate alerts when thresholds are exceeded
- Design Document: Monitoring and Performance sections
- Prometheus Documentation: https://prometheus.io/docs/
- Grafana Documentation: https://grafana.com/docs/
