# Local Bee Evaluation Setup

Complete guide for running bee evaluations locally with staging API and local MCP servers.

## Overview

This setup uses:
- **Local apiary checkout**: Runs bee from `~/dev/apiary`
- **Staging Cohere API**: Uses `CO_API_KEY_STAGING` for model access
- **Local MCP servers**: Runs tau2bench MCP servers locally on ports 8100-8102
- **BeeDB logging**: Stores all results in beedb
- **No W&B**: Wandb is disabled for local runs

## Prerequisites

1. **Apiary checkout**:
   ```bash
   cd ~/dev
   git clone git@github.com:cohere-ai/apiary.git
   ```

2. **MCP servers checkout**:
   ```bash
   cd ~/dev
   git clone git@github.com:cohere-ai/mcp.git
   ```

3. **API Keys** in `~/dev/eval-ds/.env`:
   ```bash
   CO_API_KEY_STAGING=your_staging_key_here
   # CO_API_KEY is NOT needed for local runs
   ```

## Quick Start

1. **Start MCP servers**:
   ```bash
   cd ~/dev/eval-ds
   ./experiments/scripts/manage-mcp-servers.sh start
   ```

2. **Run evaluation**:
   ```bash
   # Quick test (1 run):
   ./experiments/scripts/run-telecom-eval.sh --quick

   # Full evaluation (3 runs):
   ./experiments/scripts/run-telecom-eval.sh
   ```

## Scripts

### `manage-mcp-servers.sh`

Manages local Tau2Bench MCP servers.

**Commands**:
- `start`: Start all MCP servers (airline, retail, telecom)
- `stop`: Stop all MCP servers
- `restart`: Restart all MCP servers
- `status`: Check status of all MCP servers

**Ports**:
- Airline: 8100
- Retail: 8101
- Telecom: 8102

**Logs**: `~/.local/var/log/mcp/*.log`

### `run-bee`

Wrapper to run bee from local apiary checkout with proper environment setup.

**Usage**:
```bash
./experiments/scripts/run-bee -I path/to/config.toml [bee args...]
```

**What it does**:
1. Verifies apiary checkout exists at `~/dev/apiary`
2. Loads `.env` file for API keys
3. Validates `CO_API_KEY_STAGING` is set
4. Runs `uv run bee` from the apiary directory

### `run-telecom-eval.sh`

End-to-end script for Tau2Bench Telecom evaluation.

**Usage**:
```bash
# Full evaluation (3 runs per task):
./experiments/scripts/run-telecom-eval.sh

# Quick test (1 run per task):
./experiments/scripts/run-telecom-eval.sh --quick
```

**What it does**:
1. Loads API keys from `.env`
2. Ensures MCP servers are running (starts them if not)
3. Runs bee evaluation
4. Logs all output to `experiments/logs/tau2bench_telecom_*.log`

## Configuration Files

### `tau2bench_telecom.toml`

Full production configuration for telecom evaluation:
- 3 runs per task
- Custom preamble for c4-prod-run-1
- Uses staging API (`prod = false`)
- BeeDB logging enabled (`beedb = true`)
- W&B disabled (`wandb = false`)
- Local MCP server at `http://127.0.0.1:8102`

### `tau2bench_telecom_quick.toml`

Quick test configuration:
- 1 run per task (faster for testing)
- Lower parallelism (parallel = 2)
- Minimal sample logging (log_samples_n = 5)
- Same API/MCP setup as full config

### `tau2bench_ablation.toml`

Preamble ablation study with 4 variants:
- `baseline`: No custom preamble
- `v1_verification`: Verification-focused preamble
- `v2_efficiency`: Efficiency-focused preamble
- `v3_completeness`: Completeness-focused preamble

Includes settings from `common.toml`.

### `common.toml`

Shared settings for all evaluations:
- BeeDB enabled, W&B disabled
- Staging API (`prod = false`)
- Standard parallelism and logging settings
- Recommended settings for reasoning models

## Typical Workflow

1. **Setup** (one-time):
   ```bash
   # Clone repositories
   git clone git@github.com:cohere-ai/apiary.git ~/dev/apiary
   git clone git@github.com:cohere-ai/mcp.git ~/dev/mcp
   
   # Set up API key
   echo "CO_API_KEY_STAGING=your_key" > ~/dev/eval-ds/.env
   ```

2. **Daily development**:
   ```bash
   cd ~/dev/eval-ds
   
   # Start MCP servers
   ./experiments/scripts/manage-mcp-servers.sh start
   
   # Run quick test
   ./experiments/scripts/run-telecom-eval.sh --quick
   
   # If test passes, run full evaluation
   ./experiments/scripts/run-telecom-eval.sh
   
   # Stop MCP servers when done
   ./experiments/scripts/manage-mcp-servers.sh stop
   ```

3. **Viewing results**:
   - Check terminal output for summary metrics
   - Query beedb for detailed results
   - Use bee viz tools for analysis

## Troubleshooting

### MCP servers won't start
Check if ports are already in use:
```bash
lsof -i :8100 -i :8101 -i :8102
```

Check logs:
```bash
tail -50 ~/.local/var/log/mcp/*.log
```

### API key errors
Verify key is set:
```bash
cd ~/dev/eval-ds
source .env
echo $CO_API_KEY_STAGING
```

### Bee can't find apiary
Check apiary exists:
```bash
ls -la ~/dev/apiary/bee
```

### Wrong MCP server
If tasks connect to remote servers instead of local:
- Check `tool_env_per_domain` in config
- Ensure `type = "http"` and `server_uri = "http://127.0.0.1:8102"`
- Restart bee after config changes

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ eval-ds (This Repository)                                    │
│                                                               │
│  ┌─────────────────┐          ┌──────────────────────┐      │
│  │ run-telecom-    │  calls   │ run-bee              │      │
│  │ eval.sh         │─────────▶│ (wrapper script)     │      │
│  └─────────────────┘          └──────────────────────┘      │
│                                         │                     │
│                                         │ exec uv run bee     │
│                                         ▼                     │
│                    ┌───────────────────────────────────────┐ │
│                    │ ~/dev/apiary                          │ │
│                    │   - bee task runner                   │ │
│                    │   - comb environment                  │ │
│                    │   - connects to staging API           │ │
│                    └───────────────────────────────────────┘ │
│                                         │                     │
│                                         │ MCP requests        │
│                                         ▼                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Local MCP Servers (~/dev/mcp)                        │   │
│  │   - airline.py  (port 8100)                          │   │
│  │   - retail.py   (port 8101)                          │   │
│  │   - telecom.py  (port 8102)                          │   │
│  │ Managed by: manage-mcp-servers.sh                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

External Services:
  ┌─────────────────────────┐    ┌──────────────────────┐
  │ Cohere Staging API      │    │ BeeDB                │
  │ (CO_API_KEY_STAGING)    │    │ (Result Storage)     │
  └─────────────────────────┘    └──────────────────────┘
```

## Notes

- **Performance**: Local MCP servers may be slower than hosted versions
- **Data**: Uses production tau2bench datasets from GCS
- **Costs**: Staging API usage may have different rate limits
- **Isolation**: Each run is fully isolated and reproducible
- **Debugging**: Set `inspect = true` in config to see sample details in stdout

