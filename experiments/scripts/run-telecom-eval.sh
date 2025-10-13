#!/bin/bash
# Run Tau2Bench Telecom evaluation locally
# Uses local apiary checkout, staging API, and local MCP servers
#
# Usage: ./run-telecom-eval.sh [--quick|--focused [--num-tasks N]]
#
# Options:
#   --quick             Run with num_runs=1 for quick testing (all 114 tasks)
#   --focused           Run first 3 tasks only for failure analysis (num_runs=1)
#   --num-tasks N       With --focused, run first N tasks (default: 3)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONFIG="${PROJECT_ROOT}/experiments/configs/tau2bench_telecom.toml"
QUICK_MODE=false
FOCUSED_MODE=false
NUM_TASKS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --focused)
            FOCUSED_MODE=true
            CONFIG="${PROJECT_ROOT}/experiments/configs/tau2bench_telecom_focused.toml"
            shift
            ;;
        --num-tasks)
            if [[ -n "${2:-}" ]] && [[ "$2" =~ ^[0-9]+$ ]]; then
                NUM_TASKS="$2"
                shift 2
            else
                echo "Error: --num-tasks requires a positive integer"
                exit 1
            fi
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: $0 [--quick|--focused [--num-tasks N]]"
            exit 1
            ;;
    esac
done

# Validate arguments
if [[ -n "$NUM_TASKS" ]] && [[ "$FOCUSED_MODE" != true ]]; then
    echo "Error: --num-tasks can only be used with --focused mode"
    exit 1
fi

# Change to project root
cd "${PROJECT_ROOT}"

# Load environment variables (API keys)
if [ -f "${PROJECT_ROOT}/.env" ]; then
    echo "📋 Loading environment variables from .env..."
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
fi

# Verify API key
if [ -z "${CO_API_KEY_STAGING:-}" ]; then
    echo "❌ Error: CO_API_KEY_STAGING not set"
    echo "Please add it to ${PROJECT_ROOT}/.env"
    exit 1
fi

# Ensure MCP servers are running
echo "🔍 Checking MCP servers..."
if ! "${SCRIPT_DIR}/manage-mcp-servers.sh" status >/dev/null 2>&1; then
    echo "🚀 Starting MCP servers..."
    "${SCRIPT_DIR}/manage-mcp-servers.sh" start
    echo ""
else
    echo "✅ MCP servers already running"
    echo ""
fi

# Create log directory
LOG_DIR="${PROJECT_ROOT}/experiments/logs"
mkdir -p "${LOG_DIR}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/tau2bench_telecom_${TIMESTAMP}.log"

# Print configuration
echo "========================================="
echo "Tau2Bench Telecom Evaluation"
echo "========================================="
echo "Config: ${CONFIG}"
echo "Mode: LOCAL (using apiary checkout)"
echo "API: Staging (CO_API_KEY_STAGING)"
echo "Log file: ${LOG_FILE}"
echo ""

if [ "$FOCUSED_MODE" = true ]; then
    # Determine number of tasks (default 3, or custom from --num-tasks)
    TASKS_TO_RUN="${NUM_TASKS:-3}"
    echo "🔬 Focused mode: Running first ${TASKS_TO_RUN} tasks for failure analysis"
    echo ""
    
    if [[ -n "$NUM_TASKS" ]]; then
        # Override num_truncate with custom value
        BEE_ARGS=("-I" "${CONFIG}" "--options" "--num_truncate" "${NUM_TASKS}")
    else
        # Use default from config file (3 tasks)
        BEE_ARGS=("-I" "${CONFIG}")
    fi
elif [ "$QUICK_MODE" = true ]; then
    echo "⚡ Quick mode: Running with num_runs=1"
    echo ""
    BEE_ARGS=("-I" "${CONFIG}" "--options" "--num_runs" "1")
else
    BEE_ARGS=("-I" "${CONFIG}")
fi

echo "Starting evaluation at: $(date)"
echo "========================================="
echo ""

# Run bee evaluation with filtered output
# Note: Preamble patch is automatically applied by run_bee_with_patch.py
# 
# The filter script removes verbose streaming logs and adds task completion counter
"${SCRIPT_DIR}/run-bee" "${BEE_ARGS[@]}" 2>&1 | \
    tee "${LOG_FILE}" | \
    "${SCRIPT_DIR}/filter-bee-output.sh"

EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "========================================="
echo "Evaluation completed at: $(date)"
echo "Exit code: ${EXIT_CODE}"
echo "Log saved to: ${LOG_FILE}"
echo "========================================="

if [ ${EXIT_CODE} -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS!"
    echo ""
    echo "Results stored in beedb. To view:"
    echo "  1. Get run ID from the log above"
    echo "  2. Query beedb or use bee viz tools"
    echo ""
else
    echo ""
    echo "❌ Evaluation failed. Check the log:"
    echo "   cat ${LOG_FILE}"
    echo ""
fi

exit ${EXIT_CODE}
