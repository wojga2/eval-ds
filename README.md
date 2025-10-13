# Eval Data Science Tools

Tools for downloading, viewing, and analyzing bee evaluation results.

## Features

- **Download bee runs** from BeeDB to local JSONL files
- **Interactive TUI viewer** for exploring samples and results
- **TauBench reward visualization** with detailed explanations
- **Local evaluation execution** with apiary checkout

## Quick Start

### 0. Set up your environment (first time only)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone apiary (required for bee)
cd ~/dev
git clone git@github.com:cohere-ai/apiary.git

# Clone MCP servers (required for Tau2Bench)
git clone git@github.com:cohere-ai/mcp.git

# Set up API keys
cd ~/dev/eval-ds
cp .env.example .env
# Edit .env and add your CO_API_KEY_STAGING

# Sync dependencies
uv sync
```

### 1. Run bee evaluations

```bash
# Run Tau2Bench Telecom (full evaluation)
./experiments/scripts/run-telecom-eval.sh

# Quick test (1 run instead of 3)
./experiments/scripts/run-telecom-eval.sh --quick

# Focused analysis (first 3 tasks only, 1 run)
./experiments/scripts/run-telecom-eval.sh --focused
```

**See [`experiments/LOCAL_SETUP.md`](experiments/LOCAL_SETUP.md) for complete setup guide.**

### 2. Download bee run results

```bash
# Get bee_run_id from the evaluation output
uv run download-bee-run --run-id <bee_run_id>

# Downloads to output/ directory by default
# Or specify custom directory:
uv run download-bee-run --run-id <bee_run_id> --output-dir ./results
```

### 3. View samples in interactive TUI

```bash
uv run view-bee-samples output/your_downloaded_file.jsonl
```

**Keyboard shortcuts:**
- `↑`/`↓` or `j`/`k`: Navigate samples
- `→`/`←` or `l`/`h`: Switch tabs (Overview/Inputs/Outputs/Metadata)
- `q`: Quit
- `/`: Search (in sample list)

### 4. Analyze results

The TUI provides:
- Sample-by-sample navigation
- Full inputs, outputs, and metadata inspection
- TauBench reward visualization with explanations
- Score filtering and search

## Repository Structure

```
eval-ds/
├── experiments/
│   ├── configs/                        # Evaluation configurations
│   │   ├── common.toml                 # Shared settings
│   │   ├── tau2bench_telecom.toml      # Full telecom evaluation
│   │   └── tau2bench_telecom_focused.toml  # Focused (3 tasks)
│   ├── scripts/                        # Execution scripts
│   │   ├── run-bee                     # Main bee wrapper
│   │   ├── run-telecom-eval.sh         # Telecom eval runner
│   │   ├── manage-mcp-servers.sh       # MCP server management
│   │   └── run_bee_with_patch.py       # MCP patching for local servers
│   ├── logs/                           # Execution logs (gitignored)
│   ├── LOCAL_SETUP.md                  # Complete local setup guide
│   └── LOCAL_MCP_SOLUTION.md           # Technical details on MCP patching
│
├── bee_sample_viewer/                  # Interactive TUI application
│   ├── __main__.py                     # Entry point
│   ├── app.py                          # Main TUI application
│   ├── widgets.py                      # Custom textual widgets
│   └── reward_explanation.py           # TauBench reward parsing
│
├── download_bee_run.py                 # BeeDB download script
├── .env.example                        # API key template
└── pyproject.toml                      # Dependencies and scripts
```

## Configuration Files

### Example: Telecom Evaluation

`experiments/configs/tau2bench_telecom.toml`:
```toml
[includes]
common = "experiments/configs/common.toml"

[options]
version = "telecom_v1"
log_wandb_run_name = "{date} - Tau2Bench_Telecom [{estimators}]"

[task.Tau2BenchTask.Telecom]
domain = "telecom"
num_runs = 3  # Run each task 3 times

[estimator.blobheart.preamble_v1]
model = "c4-prod-run-1"
chat_preamble = """
You are an expert customer service agent...
"""
```

### Example: Focused Analysis

`experiments/configs/tau2bench_telecom_focused.toml`:
```toml
[includes]
common = "experiments/configs/common.toml"

[options]
version = "focused_analysis"
parallel = 2  # Lower parallelism

[task.Tau2BenchTask.Telecom]
domain = "telecom"
num_truncate = 3  # Only first 3 tasks
num_runs = 1  # Single run per task

[estimator.blobheart.focused]
model = "c4-prod-run-1"
```

## Local Execution Architecture

### How It Works

1. **Local Apiary**: Uses your `~/dev/apiary` checkout for bee
2. **Staging API**: Accesses models via `CO_API_KEY_STAGING`
3. **Local MCP Servers**: Runs tau2_bench MCP servers on localhost:8100-8102
4. **BeeDB Logging**: Results automatically saved to production BeeDB
5. **Runtime Patching**: `run_bee_with_patch.py` monkeypatches Tau2BenchTask to use local MCP servers

### MCP Servers

Tau2Bench requires MCP (Model Context Protocol) servers for the simulated environments:

```bash
# Start MCP servers (airline, retail, telecom)
./experiments/scripts/manage-mcp-servers.sh start

# Check status
./experiments/scripts/manage-mcp-servers.sh status

# Stop servers
./experiments/scripts/manage-mcp-servers.sh stop
```

The `run-telecom-eval.sh` script automatically starts MCP servers if they're not running.

## Comparing Results Across Runs

### Stable Identifiers

When comparing the same tasks across different runs (e.g., different preambles):

- **TauBench**: Use `inputs.env` + `inputs.index`
- **Tau2Bench**: Use `scenario_id` or `inputs.data_item.task_id`
- **NOT stable**: `sample_id` (randomly generated per run)

### Example Analysis

```python
import pandas as pd
import json

# Load two runs
baseline_samples = []
with open('output/baseline.jsonl') as f:
    for line in f:
        baseline_samples.append(json.loads(line))

preamble_v1_samples = []
with open('output/preamble_v1.jsonl') as f:
    for line in f:
        preamble_v1_samples.append(json.loads(line))

baseline = pd.DataFrame(baseline_samples)
preamble_v1 = pd.DataFrame(preamble_v1_samples)

# Extract scenario_id from inputs
baseline['scenario_id'] = baseline['inputs'].apply(lambda x: x['data_item']['task_id'])
preamble_v1['scenario_id'] = preamble_v1['inputs'].apply(lambda x: x['data_item']['task_id'])

# Join on stable identifier
comparison = pd.merge(
    baseline[['scenario_id', 'outputs']],
    preamble_v1[['scenario_id', 'outputs']],
    on='scenario_id',
    suffixes=('_baseline', '_v1')
)

# Extract rewards
comparison['reward_baseline'] = comparison['outputs_baseline'].apply(lambda x: x['reward'])
comparison['reward_v1'] = comparison['outputs_v1'].apply(lambda x: x['reward'])

# Calculate improvement
comparison['improvement'] = comparison['reward_v1'] - comparison['reward_baseline']

# Analyze
print(f"Mean improvement: {comparison['improvement'].mean():.3f}")
print(f"Win rate: {(comparison['improvement'] > 0).mean():.1%}")
print("\nTop 10 improvements:")
print(comparison.sort_values('improvement', ascending=False).head(10))
```

## Development

### Installing Dependencies

```bash
uv sync
```

### Running Tests

```bash
uv run pytest
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint
uv run ruff check .
```

## Tools Reference

### download-bee-run

Downloads complete bee run data from BeeDB.

```bash
# Basic usage
uv run download-bee-run --run-id <bee_run_id>

# Custom output directory
uv run download-bee-run --run-id <bee_run_id> --output-dir custom_dir/

# Filter tasks
uv run download-bee-run --run-id <bee_run_id> --task-filter "Telecom"

# Limit samples per task (for large tasks)
uv run download-bee-run --run-id <bee_run_id> --sample-limit 10
```

**Output**: JSONL file in output directory with all samples.

**Data included**:
- `sample_id`: Unique sample identifier (random per run)
- `prompt_hash`: Hash of input prompt (changes with preamble)
- `inputs`: Task inputs and metadata (includes stable identifiers)
- `outputs`: Model generations, rewards, trajectories
- `metrics`: Evaluation scores
- `task_run_info`: Task and estimator metadata

### view-bee-samples

Interactive TUI for viewing downloaded samples.

```bash
# View a specific file
uv run view-bee-samples output/bee_run_*.jsonl

# View with filtering
uv run view-bee-samples output/bee_run_*.jsonl
```

**Features**:
- Navigate samples with arrow keys or vim keys (j/k)
- Switch between tabs (Conversation/Reward/Metrics/Debug Info/Full Sample)
- View Tau2Bench reward analysis with detailed action comparison
- Analyze expected vs actual actions taken by the agent
- Understand evaluation criteria and where the agent failed
- Search and filter samples
- Syntax highlighting for JSON and pretty-printed output

### run-bee

Main wrapper script for running bee evaluations locally.

```bash
# Run with a config file
./experiments/scripts/run-bee -I experiments/configs/your-config.toml

# With additional options
./experiments/scripts/run-bee -I experiments/configs/your-config.toml --test --verbose
```

**How it works**:
1. Loads environment variables from `.env`
2. Verifies `~/dev/apiary` checkout exists
3. Changes to `~/dev/apiary/bee` directory
4. Runs `uv run run_bee_with_patch.py` which:
   - Monkeypatches `Tau2BenchTask.run_estimator` to use local MCP servers
   - Executes `python -m bee` with your config

## Troubleshooting

### "apiary not found"

Clone apiary to your home directory:
```bash
cd ~/dev
git clone git@github.com:cohere-ai/apiary.git
```

### "MCP servers not running"

Start the MCP servers:
```bash
./experiments/scripts/manage-mcp-servers.sh start
```

Or let the run script start them automatically:
```bash
./experiments/scripts/run-telecom-eval.sh
```

### "CO_API_KEY_STAGING not set"

Add your API key to `.env`:
```bash
cp .env.example .env
# Edit .env and add: CO_API_KEY_STAGING=your-key-here
```

### "BeeDB connection failed"

Ensure you're on the Cohere VPN or have proper network access to BeeDB.

## Contributing

1. Make changes in a feature branch
2. Run tests: `uv run pytest`
3. Lint: `uv run ruff check .`
4. Submit PR

## Support

- **Documentation**: 
  - `experiments/LOCAL_SETUP.md` - Complete setup guide
  - `experiments/LOCAL_MCP_SOLUTION.md` - Technical details
- **Slack**: #bee for questions
- **Issues**: Report to the team

---

**Happy evaluating! 🐝**
