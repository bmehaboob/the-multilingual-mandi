#!/bin/bash
# Setup script for Prometheus and Grafana monitoring
# Requirements: 18.4, 24.7

set -e

echo "========================================="
echo "Multilingual Mandi - Monitoring Setup"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Navigate to monitoring directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MONITORING_DIR="$(dirname "$SCRIPT_DIR")"
cd "$MONITORING_DIR"

echo "Step 1: Creating necessary directories..."
mkdir -p prometheus/rules
mkdir -p alertmanager
mkdir -p grafana/provisioning/datasources
mkdir -p grafana/provisioning/dashboards
mkdir -p grafana/dashboards

echo "Step 2: Validating configuration files..."

# Validate Prometheus config
if [ -f "prometheus/prometheus.yml" ]; then
    echo "✓ Prometheus configuration found"
else
    echo "✗ Prometheus configuration missing"
    exit 1
fi

# Validate alert rules
if [ -f "prometheus/rules/latency_alerts.yml" ]; then
    echo "✓ Alert rules found"
else
    echo "✗ Alert rules missing"
    exit 1
fi

# Validate Alertmanager config
if [ -f "alertmanager/alertmanager.yml" ]; then
    echo "✓ Alertmanager configuration found"
else
    echo "✗ Alertmanager configuration missing"
    exit 1
fi

# Validate Grafana provisioning
if [ -f "grafana/provisioning/datasources/prometheus.yml" ]; then
    echo "✓ Grafana datasource configuration found"
else
    echo "✗ Grafana datasource configuration missing"
    exit 1
fi

echo ""
echo "Step 3: Starting monitoring stack..."
docker-compose -f docker-compose.monitoring.yml up -d

echo ""
echo "Step 4: Waiting for services to start..."
sleep 10

# Check if services are running
echo ""
echo "Checking service status..."

if docker ps | grep -q "multilingual-mandi-prometheus"; then
    echo "✓ Prometheus is running"
else
    echo "✗ Prometheus failed to start"
fi

if docker ps | grep -q "multilingual-mandi-alertmanager"; then
    echo "✓ Alertmanager is running"
else
    echo "✗ Alertmanager failed to start"
fi

if docker ps | grep -q "multilingual-mandi-grafana"; then
    echo "✓ Grafana is running"
else
    echo "✗ Grafana failed to start"
fi

if docker ps | grep -q "multilingual-mandi-node-exporter"; then
    echo "✓ Node Exporter is running"
else
    echo "✗ Node Exporter failed to start"
fi

echo ""
echo "========================================="
echo "Monitoring Stack Setup Complete!"
echo "========================================="
echo ""
echo "Access the services at:"
echo "  - Grafana:       http://localhost:3000 (admin/admin)"
echo "  - Prometheus:    http://localhost:9090"
echo "  - Alertmanager:  http://localhost:9093"
echo ""
echo "Next steps:"
echo "  1. Change Grafana admin password on first login"
echo "  2. Configure Alertmanager email settings in alertmanager/alertmanager.yml"
echo "  3. Add the Prometheus middleware to your FastAPI app"
echo "  4. Verify metrics are being collected at http://localhost:9090/targets"
echo ""
echo "To stop the monitoring stack:"
echo "  docker-compose -f docker-compose.monitoring.yml down"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.monitoring.yml logs -f"
echo ""
