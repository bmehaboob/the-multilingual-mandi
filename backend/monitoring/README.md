# Multilingual Mandi - Monitoring Setup

This directory contains the Prometheus and Grafana monitoring stack for the Multilingual Mandi platform.

**Requirements**: 18.4, 24.7

## Overview

The monitoring stack includes:

- **Prometheus**: Metrics collection and storage
- **Alertmanager**: Alert routing and management
- **Grafana**: Visualization and dashboards
- **Node Exporter**: System metrics (CPU, memory, disk)
- **PostgreSQL Exporter**: Database metrics
- **Redis Exporter**: Cache metrics

## Quick Start

### 1. Start the Monitoring Stack

```bash
cd backend/monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. Access the Services

- **Grafana**: http://localhost:3000
  - Default credentials: admin/admin (change on first login)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### 3. View Dashboards

Navigate to Grafana and select from the available dashboards:

1. **Multilingual Mandi - System Overview**: High-level system metrics
2. **Latency Monitoring**: Detailed latency analysis and alerts

## Architecture

```
┌─────────────────┐
│   FastAPI App   │
│  (Port 8000)    │
│  /metrics       │
└────────┬────────┘
         │
         │ scrapes metrics
         ▼
┌─────────────────┐      ┌──────────────┐
│   Prometheus    │─────▶│ Alertmanager │
│  (Port 9090)    │      │ (Port 9093)  │
└────────┬────────┘      └──────┬───────┘
         │                      │
         │                      │ sends alerts
         │                      ▼
         │               ┌──────────────┐
         │               │  Email/Slack │
         │               │  Webhook     │
         │               └──────────────┘
         │
         │ data source
         ▼
┌─────────────────┐
│    Grafana      │
│  (Port 3000)    │
│  Dashboards     │
└─────────────────┘
```

## Metrics Collected

### Voice Pipeline Metrics (Requirement 18.1)

- `voice_pipeline_latency_seconds`: End-to-end voice translation latency
- `language_detection_latency_seconds`: Language detection latency
- `stt_latency_seconds`: Speech-to-text latency
- `translation_latency_seconds`: Translation latency
- `tts_latency_seconds`: Text-to-speech latency

### STT Accuracy Metrics (Requirement 18.2)

- `stt_correction_rate`: Percentage of transcriptions corrected by users
- `stt_confidence_score`: STT confidence scores distribution

### Transaction Metrics (Requirement 18.3)

- `transaction_completion_rate`: Percentage of completed transactions
- `transaction_abandonment_rate`: Percentage of abandoned transactions
- `transaction_duration_seconds`: Transaction duration distribution

### System Metrics (Requirement 24.7)

- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: HTTP request latency
- `active_users_total`: Number of active users
- `active_conversations_total`: Number of active conversations
- `db_connection_pool_usage`: Database connection pool usage
- `error_count_total`: Total errors by type and component

## Alerts (Requirement 18.4)

### Critical Alerts

1. **VoicePipelineHighLatency**: Fires when voice pipeline latency exceeds 10 seconds
2. **ServiceDown**: Fires when a service is unreachable
3. **HighErrorRate**: Fires when error rate exceeds 5%
4. **DatabaseConnectionPoolExhausted**: Fires when DB pool usage exceeds 90%

### Warning Alerts

1. **STTServiceHighLatency**: Fires when STT latency exceeds 3 seconds
2. **TranslationServiceHighLatency**: Fires when translation latency exceeds 2 seconds
3. **TTSServiceHighLatency**: Fires when TTS latency exceeds 2 seconds
4. **APIHighResponseTime**: Fires when API p99 latency exceeds 3 seconds
5. **HighSTTCorrectionRate**: Fires when STT correction rate exceeds 20%
6. **HighTransactionAbandonmentRate**: Fires when abandonment rate exceeds 30%
7. **HighCPUUsage**: Fires when CPU usage exceeds 80%
8. **HighMemoryUsage**: Fires when memory usage exceeds 85%

## Configuration

### Prometheus Configuration

Edit `prometheus/prometheus.yml` to:
- Add new scrape targets
- Adjust scrape intervals
- Configure external labels

### Alert Rules

Edit `prometheus/rules/latency_alerts.yml` to:
- Add new alert rules
- Adjust thresholds
- Modify alert labels and annotations

### Alertmanager Configuration

Edit `alertmanager/alertmanager.yml` to:
- Configure email settings
- Add Slack/PagerDuty integrations
- Adjust alert routing rules
- Configure inhibition rules

### Grafana Dashboards

Dashboards are located in `grafana/dashboards/`:
- `multilingual-mandi-overview.json`: System overview dashboard
- `latency-monitoring.json`: Detailed latency monitoring

To add new dashboards:
1. Create dashboard in Grafana UI
2. Export as JSON
3. Save to `grafana/dashboards/`
4. Restart Grafana to load

## Integration with FastAPI

### 1. Install Dependencies

```bash
pip install prometheus-client
```

### 2. Add Middleware to FastAPI App

```python
from app.middleware.prometheus_metrics import PrometheusMiddleware, metrics_endpoint
from fastapi import FastAPI

app = FastAPI()

# Add Prometheus middleware
app.add_middleware(PrometheusMiddleware)

# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    return metrics_endpoint()
```

### 3. Record Custom Metrics

```python
from app.middleware.prometheus_metrics import (
    record_voice_pipeline_latency,
    record_price_query_latency,
    update_stt_correction_rate,
    record_error
)

# Record voice pipeline latency
record_voice_pipeline_latency(
    total_latency=7.5,
    source_language="hi",
    target_language="te",
    stt_latency=2.8,
    translation_latency=1.5,
    tts_latency=1.8
)

# Record price query latency
record_price_query_latency(commodity="tomato", latency=1.2)

# Update STT correction rate
update_stt_correction_rate(language="hi", rate=0.15)

# Record error
record_error(error_type="network_timeout", component="translation_service")
```

## Monitoring Best Practices

### 1. Latency Monitoring

- Monitor p50, p95, and p99 latencies
- Set alerts at p95 or p99, not average
- Track latency by language pair to identify problematic combinations

### 2. Error Monitoring

- Track error rates, not just counts
- Group errors by type and component
- Set up alerts for sudden spikes in error rate

### 3. Resource Monitoring

- Monitor CPU, memory, and disk usage
- Set alerts before resources are exhausted (80-85% thresholds)
- Track database connection pool usage

### 4. Business Metrics

- Monitor transaction completion rates
- Track STT correction rates by language
- Monitor active users and conversations

### 5. Alert Fatigue Prevention

- Set appropriate thresholds to avoid false positives
- Use inhibition rules to suppress redundant alerts
- Group related alerts together
- Set reasonable repeat intervals

## Troubleshooting

### Prometheus Not Scraping Metrics

1. Check if FastAPI app is exposing `/metrics` endpoint:
   ```bash
   curl http://localhost:8000/metrics
   ```

2. Check Prometheus targets status:
   - Navigate to http://localhost:9090/targets
   - Verify all targets are "UP"

3. Check Prometheus logs:
   ```bash
   docker logs multilingual-mandi-prometheus
   ```

### Alerts Not Firing

1. Check alert rules are loaded:
   - Navigate to http://localhost:9090/alerts
   - Verify rules are present

2. Check Alertmanager is receiving alerts:
   - Navigate to http://localhost:9093
   - Check active alerts

3. Check Alertmanager configuration:
   ```bash
   docker logs multilingual-mandi-alertmanager
   ```

### Grafana Dashboards Not Loading

1. Check datasource connection:
   - Navigate to Configuration > Data Sources
   - Test Prometheus connection

2. Check dashboard provisioning:
   ```bash
   docker logs multilingual-mandi-grafana
   ```

3. Verify dashboard files are mounted:
   ```bash
   docker exec multilingual-mandi-grafana ls /etc/grafana/provisioning/dashboards
   ```

## Production Deployment

### Security Considerations

1. **Change Default Passwords**:
   - Grafana admin password
   - Alertmanager SMTP password

2. **Enable Authentication**:
   - Configure Grafana authentication (OAuth, LDAP, etc.)
   - Restrict Prometheus/Alertmanager access

3. **Use TLS**:
   - Enable HTTPS for Grafana
   - Use TLS for Prometheus scraping if needed

4. **Network Security**:
   - Use internal networks for monitoring services
   - Expose only Grafana to external network
   - Use firewall rules to restrict access

### Scaling Considerations

1. **Prometheus Storage**:
   - Default retention: 30 days
   - Adjust based on storage capacity
   - Consider remote storage for long-term retention

2. **High Availability**:
   - Run multiple Prometheus instances
   - Use Thanos or Cortex for HA setup
   - Run multiple Alertmanager instances

3. **Performance**:
   - Adjust scrape intervals based on load
   - Use recording rules for expensive queries
   - Optimize dashboard queries

## Maintenance

### Regular Tasks

1. **Review Alerts**:
   - Weekly review of fired alerts
   - Adjust thresholds as needed
   - Remove obsolete alerts

2. **Dashboard Updates**:
   - Add new metrics as features are added
   - Remove unused panels
   - Optimize slow queries

3. **Data Retention**:
   - Monitor Prometheus storage usage
   - Adjust retention period if needed
   - Archive old data if required

4. **Backup**:
   - Backup Grafana dashboards
   - Backup Prometheus configuration
   - Backup Alertmanager configuration

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Prometheus/Grafana logs
3. Consult the official documentation
4. Contact the platform operations team
