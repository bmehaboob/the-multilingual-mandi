#!/bin/bash

# Management script for auto-scaling operations
# Requirements: 24.3

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$DEPLOYMENT_DIR/docker-compose.prod.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if instance is running
is_instance_running() {
    local instance_name=$1
    docker-compose -f "$COMPOSE_FILE" ps -q "$instance_name" 2>/dev/null | grep -q .
}

# Function to check instance health
check_instance_health() {
    local instance_name=$1
    local port=8000
    
    if ! is_instance_running "$instance_name"; then
        echo "stopped"
        return
    fi
    
    # Try to reach health endpoint
    if curl -sf "http://localhost/health" -H "Host: $instance_name" >/dev/null 2>&1; then
        echo "healthy"
    else
        echo "unhealthy"
    fi
}

# Function to get current instance count
get_instance_count() {
    local count=0
    for i in {1..10}; do
        local instance_name="backend"
        if [ $i -gt 1 ]; then
            instance_name="backend-$i"
        fi
        
        if is_instance_running "$instance_name"; then
            count=$((count + 1))
        fi
    done
    echo $count
}

# Function to list all instances
list_instances() {
    print_info "Listing backend instances..."
    echo ""
    printf "%-15s %-10s %-10s\n" "INSTANCE" "STATUS" "HEALTH"
    printf "%-15s %-10s %-10s\n" "--------" "------" "------"
    
    for i in {1..10}; do
        local instance_name="backend"
        if [ $i -gt 1 ]; then
            instance_name="backend-$i"
        fi
        
        if is_instance_running "$instance_name"; then
            local health=$(check_instance_health "$instance_name")
            printf "%-15s %-10s %-10s\n" "$instance_name" "running" "$health"
        fi
    done
    
    echo ""
    local total=$(get_instance_count)
    print_info "Total running instances: $total"
}

# Function to scale to specific number of instances
scale_to() {
    local target=$1
    local current=$(get_instance_count)
    
    if [ -z "$target" ] || ! [[ "$target" =~ ^[0-9]+$ ]]; then
        print_error "Invalid target instance count: $target"
        exit 1
    fi
    
    if [ "$target" -lt 1 ] || [ "$target" -gt 10 ]; then
        print_error "Target instance count must be between 1 and 10"
        exit 1
    fi
    
    print_info "Current instances: $current, Target instances: $target"
    
    if [ "$target" -eq "$current" ]; then
        print_success "Already at target instance count"
        return
    fi
    
    if [ "$target" -gt "$current" ]; then
        # Scale up
        local to_add=$((target - current))
        print_info "Scaling up: adding $to_add instance(s)..."
        
        for i in $(seq $((current + 1)) $target); do
            local instance_name="backend"
            if [ $i -gt 1 ]; then
                instance_name="backend-$i"
            fi
            
            print_info "Starting $instance_name..."
            docker-compose -f "$COMPOSE_FILE" up -d "$instance_name"
            
            # Wait for instance to be healthy
            print_info "Waiting for $instance_name to be healthy..."
            local retries=30
            local healthy=false
            
            for j in $(seq 1 $retries); do
                sleep 2
                local health=$(check_instance_health "$instance_name")
                if [ "$health" = "healthy" ]; then
                    healthy=true
                    break
                fi
            done
            
            if [ "$healthy" = true ]; then
                print_success "$instance_name is healthy"
            else
                print_warning "$instance_name may not be fully healthy yet"
            fi
        done
        
        # Reload Nginx
        print_info "Reloading Nginx configuration..."
        docker-compose -f "$COMPOSE_FILE" exec -T nginx nginx -s reload
        
        print_success "Scaled up to $target instances"
    else
        # Scale down
        local to_remove=$((current - target))
        print_info "Scaling down: removing $to_remove instance(s)..."
        
        for i in $(seq $current -1 $((target + 1))); do
            local instance_name="backend"
            if [ $i -gt 1 ]; then
                instance_name="backend-$i"
            fi
            
            print_info "Stopping $instance_name..."
            docker-compose -f "$COMPOSE_FILE" stop "$instance_name"
            print_success "$instance_name stopped"
        done
        
        # Reload Nginx
        print_info "Reloading Nginx configuration..."
        docker-compose -f "$COMPOSE_FILE" exec -T nginx nginx -s reload
        
        print_success "Scaled down to $target instances"
    fi
}

# Function to get system metrics
get_metrics() {
    print_info "System Resource Utilization:"
    echo ""
    
    # CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo "CPU Usage: ${cpu_usage}%"
    
    # Memory usage
    local mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    echo "Memory Usage: ${mem_usage}%"
    
    # Disk usage
    local disk_usage=$(df -h / | tail -1 | awk '{print $5}')
    echo "Disk Usage: ${disk_usage}"
    
    # Active connections
    local connections=$(netstat -an | grep ESTABLISHED | wc -l)
    echo "Active Connections: ${connections}"
    
    echo ""
    
    # Calculate load
    local load=$(echo "scale=2; ($cpu_usage * 0.7 + ${mem_usage} * 0.3) / 100" | bc)
    echo "Calculated Load: ${load} (0.0 - 1.0)"
    
    # Scaling recommendation
    if (( $(echo "$load >= 0.80" | bc -l) )); then
        print_warning "Load is HIGH (>= 80%). Consider scaling up."
    elif (( $(echo "$load <= 0.30" | bc -l) )); then
        print_info "Load is LOW (<= 30%). Consider scaling down."
    else
        print_success "Load is within acceptable range (30% - 80%)."
    fi
}

# Function to start auto-scaler
start_autoscaler() {
    print_info "Starting auto-scaler service..."
    
    if docker-compose -f "$COMPOSE_FILE" ps -q autoscaler 2>/dev/null | grep -q .; then
        print_warning "Auto-scaler is already running"
        return
    fi
    
    docker-compose -f "$COMPOSE_FILE" up -d autoscaler
    print_success "Auto-scaler started"
    
    # Show logs
    print_info "Auto-scaler logs (Ctrl+C to exit):"
    docker-compose -f "$COMPOSE_FILE" logs -f autoscaler
}

# Function to stop auto-scaler
stop_autoscaler() {
    print_info "Stopping auto-scaler service..."
    
    if ! docker-compose -f "$COMPOSE_FILE" ps -q autoscaler 2>/dev/null | grep -q .; then
        print_warning "Auto-scaler is not running"
        return
    fi
    
    docker-compose -f "$COMPOSE_FILE" stop autoscaler
    print_success "Auto-scaler stopped"
}

# Function to show auto-scaler status
autoscaler_status() {
    if docker-compose -f "$COMPOSE_FILE" ps -q autoscaler 2>/dev/null | grep -q .; then
        print_success "Auto-scaler is running"
        echo ""
        print_info "Recent logs:"
        docker-compose -f "$COMPOSE_FILE" logs --tail=20 autoscaler
    else
        print_warning "Auto-scaler is not running"
    fi
}

# Function to show help
show_help() {
    cat << EOF
Auto-Scaling Management Script

Usage: $0 <command> [options]

Commands:
    list                    List all backend instances and their status
    scale <count>          Scale to specific number of instances (1-10)
    metrics                Show current system metrics and load
    autoscaler start       Start the auto-scaler service
    autoscaler stop        Stop the auto-scaler service
    autoscaler status      Show auto-scaler status and logs
    help                   Show this help message

Examples:
    $0 list                # List all instances
    $0 scale 5             # Scale to 5 instances
    $0 metrics             # Show system metrics
    $0 autoscaler start    # Start auto-scaler
    $0 autoscaler stop     # Stop auto-scaler

Requirements: 24.3
EOF
}

# Main script logic
main() {
    local command=$1
    shift
    
    case "$command" in
        list)
            list_instances
            ;;
        scale)
            scale_to "$1"
            ;;
        metrics)
            get_metrics
            ;;
        autoscaler)
            local subcommand=$1
            case "$subcommand" in
                start)
                    start_autoscaler
                    ;;
                stop)
                    stop_autoscaler
                    ;;
                status)
                    autoscaler_status
                    ;;
                *)
                    print_error "Unknown autoscaler subcommand: $subcommand"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
