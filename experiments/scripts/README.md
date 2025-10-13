# Experiment Scripts

Scripts for running bee evaluations.

## Setup

Before running experiments, you need a Cohere API key:

```bash
# Option 1: Use .env file (recommended)
cp .env.example .env
# Edit .env and set CO_API_KEY_STAGING=your-key-here (default: staging)
# For production models, set CO_API_KEY and add prod = true in estimator config

# Option 2: Export directly
export CO_API_KEY_STAGING="your-staging-api-key"
# Or for production: export CO_API_KEY="your-production-api-key"
```

## Scripts

### `run-bee`
Wrapper to run bee from eval-ds without apiary checkout.

**Usage:**
```bash
./run-bee --help
./run-bee -I experiments/configs/tau2bench_telecom.toml
```

**Note:** Model and estimator configurations are defined in the TOML files themselves.

### `run-telecom-eval.sh`
Run a single Tau2Bench Telecom evaluation for c4-prod-run-1.

**Usage:**
```bash
# From project root
./experiments/scripts/run-telecom-eval.sh

# Or from anywhere
cd ~/dev/eval-ds
./experiments/scripts/run-telecom-eval.sh
```

**Features:**
- Logs to `experiments/logs/telecom_eval_c4-prod-run-1_TIMESTAMP.log`
- Also outputs to stdout/stderr in real-time
- Timestamped log files
- Full error handling and exit codes

**Log Location:**
All logs are saved to `experiments/logs/` (gitignored).

## Creating New Scripts

Follow this pattern:

```bash
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/experiments/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/my_eval_${TIMESTAMP}.log"

mkdir -p "${LOG_DIR}"
cd "${PROJECT_ROOT}"

"${SCRIPT_DIR}/run-bee" -I experiments/configs/my_config.toml 2>&1 | tee "${LOG_FILE}"
```

