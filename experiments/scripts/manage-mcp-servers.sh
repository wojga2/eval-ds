#!/bin/bash
# Manage local Tau2Bench MCP servers
#
# Usage:
#   ./manage-mcp-servers.sh start    - Start all MCP servers
#   ./manage-mcp-servers.sh stop     - Stop all MCP servers
#   ./manage-mcp-servers.sh restart  - Restart all MCP servers
#   ./manage-mcp-servers.sh status   - Check status of MCP servers

set -euo pipefail

MCP_DIR="${HOME}/dev/mcp/servers/tau2_bench"
PID_DIR="${HOME}/.local/var/run/mcp"
LOG_DIR="${HOME}/.local/var/log/mcp"

# Server configurations: domain:port
# Using ports 8100-8102 to avoid conflicts with other services
SERVERS=(
    "airline:8100"
    "retail:8101"
    "telecom:8102"
)

# Ensure directories exist
mkdir -p "${PID_DIR}" "${LOG_DIR}"

start_server() {
    local domain=$1
    local port=$2
    local pid_file="${PID_DIR}/${domain}.pid"
    local log_file="${LOG_DIR}/${domain}.log"
    
    if [ -f "${pid_file}" ] && kill -0 "$(cat "${pid_file}")" 2>/dev/null; then
        echo "  ${domain}: already running (PID $(cat "${pid_file}"))"
        return
    fi
    
    echo "  ${domain}: starting on port ${port}..."
    cd "${MCP_DIR}"
    MCP_SERVER_PORT="${port}" nohup uv run "src/tau2_bench/${domain}.py" \
        > "${log_file}" 2>&1 &
    echo $! > "${pid_file}"
    
    # Wait a moment and verify it started
    sleep 2
    if kill -0 "$(cat "${pid_file}")" 2>/dev/null; then
        echo "  ${domain}: ✅ started (PID $(cat "${pid_file}"))"
    else
        echo "  ${domain}: ❌ failed to start (check ${log_file})"
        rm -f "${pid_file}"
    fi
}

stop_server() {
    local domain=$1
    local pid_file="${PID_DIR}/${domain}.pid"
    
    if [ ! -f "${pid_file}" ]; then
        echo "  ${domain}: not running"
        return
    fi
    
    local pid=$(cat "${pid_file}")
    if kill -0 "${pid}" 2>/dev/null; then
        echo "  ${domain}: stopping (PID ${pid})..."
        kill "${pid}"
        
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! kill -0 "${pid}" 2>/dev/null; then
                break
            fi
            sleep 0.5
        done
        
        # Force kill if still running
        if kill -0 "${pid}" 2>/dev/null; then
            echo "  ${domain}: force killing..."
            kill -9 "${pid}"
        fi
        
        rm -f "${pid_file}"
        echo "  ${domain}: ✅ stopped"
    else
        echo "  ${domain}: stale PID file, cleaning up"
        rm -f "${pid_file}"
    fi
}

status_server() {
    local domain=$1
    local port=$2
    local pid_file="${PID_DIR}/${domain}.pid"
    
    if [ ! -f "${pid_file}" ]; then
        echo "  ${domain}: ❌ not running"
        return 1
    fi
    
    local pid=$(cat "${pid_file}")
    if kill -0 "${pid}" 2>/dev/null; then
        # Check if port is actually listening
        if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>&1 || ss -ltn | grep -q ":${port} "; then
            echo "  ${domain}: ✅ running (PID ${pid}, port ${port})"
            return 0
        else
            echo "  ${domain}: ⚠️  process running but port ${port} not listening"
            return 1
        fi
    else
        echo "  ${domain}: ❌ not running (stale PID file)"
        rm -f "${pid_file}"
        return 1
    fi
}

case "${1:-}" in
    start)
        echo "🚀 Starting MCP servers..."
        for server in "${SERVERS[@]}"; do
            IFS=: read -r domain port <<< "${server}"
            start_server "${domain}" "${port}"
        done
        echo "✅ Done"
        ;;
        
    stop)
        echo "🛑 Stopping MCP servers..."
        for server in "${SERVERS[@]}"; do
            IFS=: read -r domain port <<< "${server}"
            stop_server "${domain}"
        done
        echo "✅ Done"
        ;;
        
    restart)
        echo "🔄 Restarting MCP servers..."
        "$0" stop
        sleep 1
        "$0" start
        ;;
        
    status)
        echo "📊 MCP server status:"
        all_running=true
        for server in "${SERVERS[@]}"; do
            IFS=: read -r domain port <<< "${server}"
            if ! status_server "${domain}" "${port}"; then
                all_running=false
            fi
        done
        
        if $all_running; then
            echo ""
            echo "✅ All servers running"
            exit 0
        else
            echo ""
            echo "⚠️  Some servers not running"
            exit 1
        fi
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

