#!/bin/bash
set -euo pipefail

# Test a single sample from tau2bench
# Usage: ./test_single_sample.sh [sample_index]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Sample index (default to 0 - the failing sample)
SAMPLE_INDEX="${1:-0}"

cd "${PROJECT_ROOT}"

# Load environment
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
fi

# Verify API key
if [ -z "${CO_API_KEY_STAGING:-}" ]; then
    echo "❌ Error: CO_API_KEY_STAGING not set"
    exit 1
fi

# Ensure MCP servers running
"${SCRIPT_DIR}/manage-mcp-servers.sh" status >/dev/null 2>&1 || "${SCRIPT_DIR}/manage-mcp-servers.sh" start

# Create temporary config for single sample test
TEMP_CONFIG="/tmp/tau2bench_single_sample_${SAMPLE_INDEX}.toml"

cat > "${TEMP_CONFIG}" << EOF
[options]
beedb = true
beedb_use_sa = true
beedb_config = "bee/utils/db_configs/config.yaml"
log_username = "wojciech_cohere_com"
log_samples = true
wandb = false
log_wandb_project = "eval-ds"
parallel = 1
attempts_per_task = 1
shuffle_tasks = false
skip_completed_tasks = false
version = "single_sample_test_${SAMPLE_INDEX}_iteration_\${ITERATION:-0}"

[options.summary_metrics.Tau2Bench_Telecom]
"Tau2BenchTask.Telecom:total_reward" = 1.0

[estimator-defaults]
k = 0
p = 1.0
temperature = 0.6
thinking_enabled = true
prod = false

[task.Tau2BenchTask.Telecom]
domain = "telecom"
num_runs = 1
num_truncate = $((SAMPLE_INDEX + 1))
num_truncate_per_source = ${SAMPLE_INDEX}
prompt_patches = ["TOOL_CONFUSION_AGENT_VS_USER"]

[estimator.blobheart.test]
model = "c4-prod-run-1"
EOF

echo "🧪 Testing sample index ${SAMPLE_INDEX}"
echo "   Config: ${TEMP_CONFIG}"
echo ""

# Run bee
"${SCRIPT_DIR}/run-bee" -I "${TEMP_CONFIG}" 2>&1 | tee "/tmp/bee_test_sample_${SAMPLE_INDEX}.log"

EXIT_CODE=${PIPESTATUS[0]}

if [ ${EXIT_CODE} -eq 0 ]; then
    echo ""
    echo "✅ Test completed"
    # Extract run ID
    RUN_ID=$(grep "bee_run_id:" "/tmp/bee_test_sample_${SAMPLE_INDEX}.log" | head -1 | awk '{print $NF}')
    echo "   Run ID: ${RUN_ID}"
    echo "${RUN_ID}" > "/tmp/last_test_run_id.txt"
else
    echo ""
    echo "❌ Test failed with exit code ${EXIT_CODE}"
fi

exit ${EXIT_CODE}

