#!/bin/bash

# Failure Viewer App Control Script
# Usage: ./failure-viewer-app-control.sh [start|stop|restart|status|logs]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_DIR="$SCRIPT_DIR/.pids"
LOGS_DIR="$SCRIPT_DIR/logs"

# Backend and Frontend ports
BACKEND_PORT=9000
FRONTEND_PORT=9001

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create directories if they don't exist
mkdir -p "$PID_DIR"
mkdir -p "$LOGS_DIR"

# Print colored output
print_status() {
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

# Get Tailscale IP address
get_tailscale_ip() {
    if command -v tailscale > /dev/null 2>&1; then
        local tailscale_ip=$(tailscale ip --4 2>/dev/null | head -n1)
        if [ -n "$tailscale_ip" ] && [ "$tailscale_ip" != "" ]; then
            echo "$tailscale_ip"
            return 0
        fi
    fi
    echo ""
    return 1
}

# Check if a process is running
is_process_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Kill process by PID file
kill_process() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_status "Stopping $service_name (PID: $pid)..."
            kill "$pid"
            
            # Wait up to 10 seconds for graceful shutdown
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                print_warning "Force killing $service_name..."
                kill -9 "$pid"
            fi
            
            print_success "$service_name stopped"
        fi
        rm -f "$pid_file"
    fi
}

# Wait for service to be ready
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_attempts=30
    local attempt=0
    
    print_status "Waiting for $service_name to be ready on port $port..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "http://127.0.0.1:$port" > /dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
        echo -n "."
    done
    
    echo ""
    print_error "$service_name failed to start within ${max_attempts} seconds"
    return 1
}

# Start backend
start_backend() {
    local backend_pid_file="$PID_DIR/backend.pid"
    local backend_log_file="$LOGS_DIR/backend.log"
    
    if is_process_running "$backend_pid_file"; then
        print_warning "Backend is already running"
        return 0
    fi
    
    print_status "Starting backend server on port $BACKEND_PORT..."
    
    # Navigate to project root
    cd "$PROJECT_ROOT"
    
    # Install/sync Python dependencies
    print_status "Syncing Python dependencies with uv..."
    uv sync > /dev/null 2>&1
    
    # Start backend in background
    nohup uv run python -c "
import uvicorn
import sys
import os
sys.path.append('failure_viewer_app/backend')
from main import app
uvicorn.run(app, host='0.0.0.0', port=$BACKEND_PORT)
" > "$backend_log_file" 2>&1 &
    
    local backend_pid=$!
    echo "$backend_pid" > "$backend_pid_file"
    
    print_success "Backend started with PID: $backend_pid"
    print_status "Backend logs: $backend_log_file"
    print_status "Backend URL: http://127.0.0.1:$BACKEND_PORT"
}

# Start frontend
start_frontend() {
    local frontend_pid_file="$PID_DIR/frontend.pid"
    local frontend_log_file="$LOGS_DIR/frontend.log"
    
    if is_process_running "$frontend_pid_file"; then
        print_warning "Frontend is already running"
        return 0
    fi
    
    print_status "Starting frontend server on port $FRONTEND_PORT..."
    
    cd "$SCRIPT_DIR/frontend"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_status "Installing Node.js dependencies..."
        npm install
    fi
    
    # Start frontend in background
    nohup npm run dev > "$frontend_log_file" 2>&1 &
    local frontend_pid=$!
    echo "$frontend_pid" > "$frontend_pid_file"
    
    print_success "Frontend started with PID: $frontend_pid"
    print_status "Frontend logs: $frontend_log_file"
    print_status "Frontend URL: http://127.0.0.1:$FRONTEND_PORT"
}

# Start all services
start_services() {
    print_status "🚀 Starting Failure Viewer App..."
    echo "=============================================="
    
    # Check prerequisites
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js v18 or higher."
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.10 or higher."
        exit 1
    fi
    
    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed. Please install uv for Python dependency management."
        exit 1
    fi
    
    # Start services
    start_backend
    start_frontend
    
    # Wait for services to be ready
    if wait_for_service "$BACKEND_PORT" "Backend"; then
        if wait_for_service "$FRONTEND_PORT" "Frontend"; then
            echo ""
            print_success "🎉 Failure Viewer App is ready!"
            echo "=============================================="
            
            # Get Tailscale IP
            local tailscale_ip=$(get_tailscale_ip)
            
            if [ -n "$tailscale_ip" ]; then
                print_status "🌐 Access via Tailscale:"
                echo ""
                print_success "   Frontend: http://$tailscale_ip:$FRONTEND_PORT"
                print_status "   Backend:  http://$tailscale_ip:$BACKEND_PORT"
                echo ""
                print_status "🏠 Local access:"
                print_status "   Frontend: http://127.0.0.1:$FRONTEND_PORT"
                print_status "   Backend:  http://127.0.0.1:$BACKEND_PORT"
            else
                print_status "Backend:  http://127.0.0.1:$BACKEND_PORT"
                print_status "Frontend: http://127.0.0.1:$FRONTEND_PORT"
                print_warning "Tailscale not available - using localhost only"
            fi
            
            echo ""
            print_status "💡 To stop the app, run: $0 stop"
            print_status "📊 To check status, run: $0 status"
            print_status "📋 View logs: tail -f $LOGS_DIR/*.log"
        else
            print_error "Frontend failed to start properly"
            stop_services
            exit 1
        fi
    else
        print_error "Backend failed to start properly"
        stop_services
        exit 1
    fi
}

# Stop all services
stop_services() {
    local backend_pid_file="$PID_DIR/backend.pid"
    local frontend_pid_file="$PID_DIR/frontend.pid"
    
    print_status "🛑 Stopping Failure Viewer App..."
    echo "=============================================="
    
    kill_process "$frontend_pid_file" "Frontend"
    kill_process "$backend_pid_file" "Backend"
    
    print_success "All services stopped"
}

# Show status
show_status() {
    local backend_pid_file="$PID_DIR/backend.pid"
    local frontend_pid_file="$PID_DIR/frontend.pid"
    
    print_status "📊 Failure Viewer App Status"
    echo "=============================================="
    
    if is_process_running "$backend_pid_file"; then
        local backend_pid=$(cat "$backend_pid_file")
        print_success "Backend: RUNNING (PID: $backend_pid) - http://127.0.0.1:$BACKEND_PORT"
    else
        print_error "Backend: STOPPED"
    fi
    
    if is_process_running "$frontend_pid_file"; then
        local frontend_pid=$(cat "$frontend_pid_file")
        print_success "Frontend: RUNNING (PID: $frontend_pid) - http://127.0.0.1:$FRONTEND_PORT"
    else
        print_error "Frontend: STOPPED"
    fi
    
    echo ""
    
    if is_process_running "$backend_pid_file" && is_process_running "$frontend_pid_file"; then
        print_success "✅ All services are running"
        echo ""
        
        # Get Tailscale IP
        local tailscale_ip=$(get_tailscale_ip)
        
        if [ -n "$tailscale_ip" ]; then
            print_status "🌐 Access via Tailscale:"
            print_success "   Frontend: http://$tailscale_ip:$FRONTEND_PORT"
            print_status "   Backend:  http://$tailscale_ip:$BACKEND_PORT"
            echo ""
            print_status "🏠 Local: http://127.0.0.1:$FRONTEND_PORT"
        else
            print_status "🌐 Access the app at: http://127.0.0.1:$FRONTEND_PORT"
        fi
    elif is_process_running "$backend_pid_file" || is_process_running "$frontend_pid_file"; then
        print_warning "⚠️ Some services are running, some are stopped"
    else
        print_warning "❌ All services are stopped"
        echo ""
        print_status "💡 To start services, run: $0 start"
    fi
}

# Show logs
show_logs() {
    print_status "📋 Showing logs (Ctrl+C to exit)..."
    echo "=============================================="
    tail -f "$LOGS_DIR"/*.log
}

# Main script logic
case "${1:-}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        print_status "🔄 Restarting Failure Viewer App..."
        stop_services
        sleep 2
        start_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 [start|stop|restart|status|logs]"
        echo ""
        echo "Commands:"
        echo "  start     - Start backend and frontend servers"
        echo "  stop      - Stop all services"
        echo "  restart   - Stop and start all services"
        echo "  status    - Show status of all services"
        echo "  logs      - Tail all logs"
        echo ""
        echo "Ports:"
        echo "  Backend:  $BACKEND_PORT"
        echo "  Frontend: $FRONTEND_PORT"
        exit 1
        ;;
esac

