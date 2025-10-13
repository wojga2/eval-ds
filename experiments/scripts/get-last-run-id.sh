#!/bin/bash
# Get the bee_run_id from the most recent local evaluation
#
# Usage:
#   ./experiments/scripts/get-last-run-id.sh
#   ./experiments/scripts/get-last-run-id.sh --download
#   ./experiments/scripts/get-last-run-id.sh --view

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/experiments/logs"

# Find the most recent log file
LATEST_LOG=$(ls -t "${LOG_DIR}"/tau2bench_*.log 2>/dev/null | head -1)

if [ -z "${LATEST_LOG}" ]; then
    echo "❌ No log files found in ${LOG_DIR}"
    exit 1
fi

# Extract bee_run_id
BEE_RUN_ID=$(grep -o 'bee_run_id: [a-f0-9-]*' "${LATEST_LOG}" | head -1 | awk '{print $2}')

if [ -z "${BEE_RUN_ID}" ]; then
    echo "❌ Could not find bee_run_id in ${LATEST_LOG}"
    exit 1
fi

echo "📋 Most recent run:"
echo "   Log: $(basename ${LATEST_LOG})"
echo "   Bee run ID: ${BEE_RUN_ID}"
echo ""

# Handle command line options
case "${1:-}" in
    --download)
        echo "📥 Downloading results..."
        cd "${PROJECT_ROOT}"
        uv run download-bee-run "${BEE_RUN_ID}"
        ;;
    --view)
        echo "👁️  Opening viewer..."
        cd "${PROJECT_ROOT}"
        uv run view-bee-samples output/task_*.jsonl
        ;;
    *)
        echo "💡 To download results:"
        echo "   uv run download-bee-run ${BEE_RUN_ID}"
        echo ""
        echo "💡 Or use shortcuts:"
        echo "   ./experiments/scripts/get-last-run-id.sh --download"
        echo "   ./experiments/scripts/get-last-run-id.sh --view"
        ;;
esac

