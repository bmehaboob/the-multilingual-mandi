#!/bin/bash

# Health Check Script for Multilingual Mandi Backend Instances
# This script checks the health of all backend instances and reports their status
# Requirements: 24.5 - Load balancing with health monitoring

set -e

# Configuration
BACKEND_INSTANCES=(
    "backend:8000"
    "backend-2:8000"
    "backend-3:8000"
)

HEALTH_ENDPOINT="/health"
TIMEOUT=5
RETRY_COUNT=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check health of a single backend
check_backend_health() {
    local backend=$1
    local url="http://${backend}${HEALTH_ENDPOINT}"
    
    echo -n "Checking ${backend}... "
    
    # Try to reach the health endpoint
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout ${TIMEOUT} --max-time ${TIMEOUT} "${url}" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ HEALTHY${NC} (HTTP ${response})"
        return 0
    elif [ "$response" = "000" ]; then
        echo -e "${RED}✗ UNREACHABLE${NC} (Connection failed)"
        return 1
    else
        echo -e "${YELLOW}⚠ UNHEALTHY${NC} (HTTP ${response})"
        return 1
    fi
}

# Function to get detailed health info
get_detailed_health() {
    local backend=$1
    local url="http://${backend}${HEALTH_ENDPOINT}"
    
    echo "Detailed health info for ${backend}:"
    response=$(curl -s --connect-timeout ${TIMEOUT} --max-time ${TIMEOUT} "${url}" 2>/dev/null || echo "{\"error\": \"unreachable\"}")
    echo "${response}" | python3 -m json.tool 2>/dev/null || echo "${response}"
    echo ""
}

# Function to check all backends
check_all_backends() {
    local healthy_count=0
    local total_count=${#BACKEND_INSTANCES[@]}
    
    echo "=========================================="
    echo "Backend Health Check Report"
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=========================================="
    echo ""
    
    for backend in "${BACKEND_INSTANCES[@]}"; do
        if check_backend_health "${backend}"; then
            ((healthy_count++))
        fi
    done
    
    echo ""
    echo "=========================================="
    echo "Summary: ${healthy_count}/${total_count} backends healthy"
    echo "=========================================="
    
    if [ ${healthy_count} -eq 0 ]; then
        echo -e "${RED}CRITICAL: All backends are down!${NC}"
        return 2
    elif [ ${healthy_count} -lt ${total_count} ]; then
        echo -e "${YELLOW}WARNING: Some backends are unhealthy${NC}"
        return 1
    else
        echo -e "${GREEN}OK: All backends are healthy${NC}"
        return 0
    fi
}

# Function to monitor backends continuously
monitor_backends() {
    local interval=${1:-30}
    
    echo "Starting continuous health monitoring (interval: ${interval}s)"
    echo "Press Ctrl+C to stop"
    echo ""
    
    while true; do
        check_all_backends
        echo ""
        echo "Next check in ${interval} seconds..."
        echo ""
        sleep ${interval}
    done
}

# Function to check load distribution
check_load_distribution() {
    echo "=========================================="
    echo "Load Distribution Check"
    echo "=========================================="
    echo ""
    
    for backend in "${BACKEND_INSTANCES[@]}"; do
        local url="http://${backend}/metrics"
        echo "Backend: ${backend}"
        
        # Try to get metrics (if available)
        metrics=$(curl -s --connect-timeout ${TIMEOUT} --max-time ${TIMEOUT} "${url}" 2>/dev/null || echo "")
        
        if [ -n "${metrics}" ]; then
            # Extract relevant metrics (adjust based on your metrics format)
            echo "${metrics}" | grep -E "(request_count|active_connections|cpu_usage)" || echo "  Metrics not available"
        else
            echo "  Metrics endpoint not available"
        fi
        echo ""
    done
}

# Function to test failover
test_failover() {
    local test_backend=${1:-"backend:8000"}
    
    echo "=========================================="
    echo "Failover Test"
    echo "=========================================="
    echo ""
    echo "This test simulates a backend failure to verify failover behavior"
    echo "Target backend: ${test_backend}"
    echo ""
    echo "WARNING: This will temporarily mark the backend as down"
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Test cancelled"
        return 0
    fi
    
    echo "1. Checking initial state..."
    check_all_backends
    
    echo ""
    echo "2. Simulating backend failure..."
    echo "   (In production, you would mark the server as 'down' in nginx config)"
    echo "   docker-compose stop ${test_backend%%:*}"
    
    echo ""
    echo "3. Verify that requests are routed to other backends"
    echo "   Make test requests and check nginx access logs"
    
    echo ""
    echo "4. Restore backend and verify recovery"
    echo "   docker-compose start ${test_backend%%:*}"
}

# Main script
main() {
    case "${1:-check}" in
        check)
            check_all_backends
            exit $?
            ;;
        monitor)
            monitor_backends "${2:-30}"
            ;;
        detailed)
            echo "=========================================="
            echo "Detailed Health Information"
            echo "=========================================="
            echo ""
            for backend in "${BACKEND_INSTANCES[@]}"; do
                get_detailed_health "${backend}"
            done
            ;;
        load)
            check_load_distribution
            ;;
        failover)
            test_failover "${2}"
            ;;
        help|--help|-h)
            echo "Usage: $0 [command] [options]"
            echo ""
            echo "Commands:"
            echo "  check           Check health of all backends once (default)"
            echo "  monitor [sec]   Continuously monitor backends (default: 30s interval)"
            echo "  detailed        Get detailed health information from all backends"
            echo "  load            Check load distribution across backends"
            echo "  failover [host] Test failover behavior (interactive)"
            echo "  help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Check health once"
            echo "  $0 monitor 60         # Monitor every 60 seconds"
            echo "  $0 detailed           # Get detailed health info"
            echo "  $0 load               # Check load distribution"
            ;;
        *)
            echo "Unknown command: $1"
            echo "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
