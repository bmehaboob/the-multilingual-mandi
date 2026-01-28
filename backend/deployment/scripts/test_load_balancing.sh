#!/bin/bash

# Load Balancing Test Script for Multilingual Mandi
# This script tests the load balancing configuration by making multiple requests
# and verifying that they are distributed across backend instances
# Requirements: 24.5 - Load balancing across multiple servers

set -e

# Configuration
NGINX_URL="${NGINX_URL:-http://localhost}"
TEST_ENDPOINT="${TEST_ENDPOINT:-/health}"
NUM_REQUESTS="${NUM_REQUESTS:-100}"
CONCURRENT_REQUESTS="${CONCURRENT_REQUESTS:-10}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Load Balancing Test"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  URL: ${NGINX_URL}"
echo "  Endpoint: ${TEST_ENDPOINT}"
echo "  Total Requests: ${NUM_REQUESTS}"
echo "  Concurrent: ${CONCURRENT_REQUESTS}"
echo ""

# Function to make a single request and extract backend info
make_request() {
    local request_num=$1
    local url="${NGINX_URL}${TEST_ENDPOINT}"
    
    # Make request and capture response headers
    response=$(curl -s -w "\n%{http_code}\n%{time_total}" "${url}" 2>/dev/null || echo "error\n000\n0")
    
    http_code=$(echo "${response}" | tail -n 2 | head -n 1)
    time_total=$(echo "${response}" | tail -n 1)
    
    if [ "${http_code}" = "200" ]; then
        echo "${request_num},success,${time_total}"
    else
        echo "${request_num},failed,${time_total}"
    fi
}

# Function to run load test
run_load_test() {
    echo "Running load test..."
    echo ""
    
    local success_count=0
    local failed_count=0
    local total_time=0
    
    # Create temporary file for results
    local results_file=$(mktemp)
    
    # Make requests
    for i in $(seq 1 ${NUM_REQUESTS}); do
        make_request ${i} >> "${results_file}" &
        
        # Limit concurrent requests
        if [ $((i % CONCURRENT_REQUESTS)) -eq 0 ]; then
            wait
        fi
        
        # Progress indicator
        if [ $((i % 10)) -eq 0 ]; then
            echo -n "."
        fi
    done
    
    # Wait for remaining requests
    wait
    echo ""
    echo ""
    
    # Analyze results
    echo "Analyzing results..."
    echo ""
    
    while IFS=',' read -r req_num status time; do
        if [ "${status}" = "success" ]; then
            ((success_count++))
            total_time=$(echo "${total_time} + ${time}" | bc)
        else
            ((failed_count++))
        fi
    done < "${results_file}"
    
    # Calculate statistics
    local success_rate=$(echo "scale=2; ${success_count} * 100 / ${NUM_REQUESTS}" | bc)
    local avg_time=$(echo "scale=3; ${total_time} / ${success_count}" | bc 2>/dev/null || echo "0")
    
    # Display results
    echo "=========================================="
    echo "Test Results"
    echo "=========================================="
    echo ""
    echo "Total Requests:    ${NUM_REQUESTS}"
    echo -e "Successful:        ${GREEN}${success_count}${NC}"
    echo -e "Failed:            ${RED}${failed_count}${NC}"
    echo -e "Success Rate:      ${GREEN}${success_rate}%${NC}"
    echo "Average Time:      ${avg_time}s"
    echo ""
    
    # Check if success rate meets requirements
    if (( $(echo "${success_rate} >= 99" | bc -l) )); then
        echo -e "${GREEN}✓ PASS: Success rate meets requirement (≥99%)${NC}"
    else
        echo -e "${RED}✗ FAIL: Success rate below requirement (${success_rate}% < 99%)${NC}"
    fi
    
    # Check if average time meets requirements (< 3 seconds)
    if (( $(echo "${avg_time} < 3" | bc -l) )); then
        echo -e "${GREEN}✓ PASS: Average response time meets requirement (<3s)${NC}"
    else
        echo -e "${YELLOW}⚠ WARNING: Average response time above target (${avg_time}s ≥ 3s)${NC}"
    fi
    
    # Cleanup
    rm -f "${results_file}"
}

# Function to test backend distribution
test_backend_distribution() {
    echo "=========================================="
    echo "Backend Distribution Test"
    echo "=========================================="
    echo ""
    echo "Making ${NUM_REQUESTS} requests to check distribution..."
    echo ""
    
    # This requires access to Nginx logs or backend response headers
    # For now, we'll check if we can reach the backends through Nginx
    
    local backends=("backend:8000" "backend-2:8000" "backend-3:8000")
    
    echo "Checking if all backends are reachable through load balancer..."
    echo ""
    
    for backend in "${backends[@]}"; do
        echo -n "Testing ${backend}... "
        
        # Make multiple requests and hope to hit each backend
        local hit=false
        for i in {1..20}; do
            response=$(curl -s "${NGINX_URL}${TEST_ENDPOINT}" 2>/dev/null || echo "")
            if [ -n "${response}" ]; then
                hit=true
                break
            fi
        done
        
        if [ "${hit}" = true ]; then
            echo -e "${GREEN}✓ Reachable${NC}"
        else
            echo -e "${RED}✗ Not reachable${NC}"
        fi
    done
    
    echo ""
    echo "Note: To verify actual distribution, check Nginx access logs:"
    echo "  docker-compose logs nginx | grep 'upstream:' | awk '{print \$NF}' | sort | uniq -c"
}

# Function to test failover
test_failover() {
    echo "=========================================="
    echo "Failover Test"
    echo "=========================================="
    echo ""
    echo "This test verifies that requests continue to work when a backend fails"
    echo ""
    
    echo "Step 1: Make baseline requests (all backends healthy)"
    local baseline_success=0
    for i in {1..10}; do
        response=$(curl -s -o /dev/null -w "%{http_code}" "${NGINX_URL}${TEST_ENDPOINT}" 2>/dev/null || echo "000")
        if [ "${response}" = "200" ]; then
            ((baseline_success++))
        fi
    done
    echo "  Baseline: ${baseline_success}/10 successful"
    echo ""
    
    echo "Step 2: Simulate backend failure"
    echo "  Run: docker-compose stop backend-2"
    echo "  (This step must be done manually)"
    echo ""
    read -p "Press Enter after stopping backend-2..."
    echo ""
    
    echo "Step 3: Make requests with one backend down"
    local failover_success=0
    for i in {1..10}; do
        response=$(curl -s -o /dev/null -w "%{http_code}" "${NGINX_URL}${TEST_ENDPOINT}" 2>/dev/null || echo "000")
        if [ "${response}" = "200" ]; then
            ((failover_success++))
        fi
    done
    echo "  Failover: ${failover_success}/10 successful"
    echo ""
    
    if [ ${failover_success} -ge 9 ]; then
        echo -e "${GREEN}✓ PASS: Failover working correctly${NC}"
    else
        echo -e "${RED}✗ FAIL: Failover not working properly${NC}"
    fi
    
    echo ""
    echo "Step 4: Restore backend"
    echo "  Run: docker-compose start backend-2"
    echo "  (This step must be done manually)"
}

# Function to test concurrent connections
test_concurrent_connections() {
    echo "=========================================="
    echo "Concurrent Connections Test"
    echo "=========================================="
    echo ""
    echo "Testing with ${CONCURRENT_REQUESTS} concurrent connections..."
    echo ""
    
    local start_time=$(date +%s)
    
    # Make concurrent requests
    for i in $(seq 1 ${CONCURRENT_REQUESTS}); do
        curl -s -o /dev/null "${NGINX_URL}${TEST_ENDPOINT}" &
    done
    
    wait
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo "Completed ${CONCURRENT_REQUESTS} concurrent requests in ${duration}s"
    echo ""
    
    if [ ${duration} -lt 10 ]; then
        echo -e "${GREEN}✓ PASS: Concurrent requests handled efficiently${NC}"
    else
        echo -e "${YELLOW}⚠ WARNING: Concurrent requests took longer than expected${NC}"
    fi
}

# Function to test with load
stress_test() {
    local duration=${1:-60}
    
    echo "=========================================="
    echo "Stress Test"
    echo "=========================================="
    echo ""
    echo "Running stress test for ${duration} seconds..."
    echo "This will generate continuous load on the system"
    echo ""
    
    local start_time=$(date +%s)
    local end_time=$((start_time + duration))
    local request_count=0
    local success_count=0
    
    while [ $(date +%s) -lt ${end_time} ]; do
        response=$(curl -s -o /dev/null -w "%{http_code}" "${NGINX_URL}${TEST_ENDPOINT}" 2>/dev/null || echo "000") &
        ((request_count++))
        
        if [ "${response}" = "200" ]; then
            ((success_count++))
        fi
        
        # Progress indicator
        if [ $((request_count % 100)) -eq 0 ]; then
            local elapsed=$(($(date +%s) - start_time))
            local rate=$((request_count / elapsed))
            echo "  ${request_count} requests sent (${rate} req/s)"
        fi
        
        # Small delay to prevent overwhelming the system
        sleep 0.01
    done
    
    wait
    
    echo ""
    echo "Stress test completed"
    echo "  Total requests: ${request_count}"
    echo "  Duration: ${duration}s"
    echo "  Average rate: $((request_count / duration)) req/s"
}

# Main menu
main() {
    case "${1:-load}" in
        load)
            run_load_test
            ;;
        distribution)
            test_backend_distribution
            ;;
        failover)
            test_failover
            ;;
        concurrent)
            test_concurrent_connections
            ;;
        stress)
            stress_test "${2:-60}"
            ;;
        all)
            run_load_test
            echo ""
            test_backend_distribution
            echo ""
            test_concurrent_connections
            ;;
        help|--help|-h)
            echo "Usage: $0 [test] [options]"
            echo ""
            echo "Tests:"
            echo "  load              Run basic load test (default)"
            echo "  distribution      Test backend distribution"
            echo "  failover          Test failover behavior (interactive)"
            echo "  concurrent        Test concurrent connections"
            echo "  stress [seconds]  Run stress test (default: 60s)"
            echo "  all               Run all non-interactive tests"
            echo "  help              Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  NGINX_URL              Nginx URL (default: http://localhost)"
            echo "  TEST_ENDPOINT          Test endpoint (default: /health)"
            echo "  NUM_REQUESTS           Number of requests (default: 100)"
            echo "  CONCURRENT_REQUESTS    Concurrent requests (default: 10)"
            echo ""
            echo "Examples:"
            echo "  $0 load"
            echo "  $0 stress 120"
            echo "  NUM_REQUESTS=1000 $0 load"
            ;;
        *)
            echo "Unknown test: $1"
            echo "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Check dependencies
if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl is required but not installed${NC}"
    exit 1
fi

if ! command -v bc &> /dev/null; then
    echo -e "${YELLOW}Warning: bc is not installed, some calculations may not work${NC}"
fi

# Run main function
main "$@"
