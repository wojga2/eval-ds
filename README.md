# Bee Run Data Tools

Tools for downloading, viewing, and running bee evaluations with full metadata and agentic trajectories.

## Features

- 📥 **Download** bee run samples from BeeDB with full trajectories
- 👀 **View** samples in an interactive TUI with reward explanations (TauBench)
- 🧪 **Run** bee experiments with custom preambles (no apiary checkout needed!)

## Quick Start

```bash
# 1. Download samples from a bee run
uv run download-bee-run --run-id "your-bee-run-id"

# 2. View samples in an interactive TUI
uv run view-bee-samples output/task_*.jsonl

# 3. Run bee experiments (self-contained!)
uv run --with bee --python 3.11 python -m bee -I experiments/tau2bench_telecom.toml \
    --estimator blobheart --model c4-prod-run-1
```

## Running Bee Experiments (Self-Contained)

This repo includes everything you need to run bee experiments without the apiary checkout:

### Single Preamble Test

```bash
cd ~/dev/eval-ds

# Quick test (5 samples)
uv run --with bee --python 3.11 python -m bee --test \
    -I experiments/tau2bench_telecom.toml \
    --estimator blobheart --model c4-prod-run-1

# Full run
uv run --with bee --python 3.11 python -m bee \
    -I experiments/tau2bench_telecom.toml \
    --estimator blobheart --model c4-prod-run-1
```

### Preamble Ablation Study (4 variants)

```bash
cd ~/dev/eval-ds

uv run --with bee --python 3.11 python -m bee \
    -I experiments/tau2bench_ablation.toml \
    --estimator blobheart --model c4-prod-run-1 \
    --estimator blobheart --model c4-prod-run-1 \
    --estimator blobheart --model c4-prod-run-1 \
    --estimator blobheart --model c4-prod-run-1
```

### Create Your Own Experiments

Store your experiment configs in `experiments/` directory:

```toml
# experiments/my_experiment.toml
[options]
wandb = true
log_wandb_run_name = "{date} - My Experiment [{estimators}]"

[task.Tau2BenchTask.Telecom]
domain = "telecom"
num_runs = 3

[estimator.blobheart]
chat_preamble = "Your custom preamble..."
```

## Download Usage

```bash
# Download all samples from a bee run
uv run download-bee-run --run-id "your-bee-run-id"

# Download specific task
uv run download-bee-run \
    --task-run-id "your-task-run-id" \
    --run-id "your-bee-run-id"

# With filters and limits
uv run download-bee-run \
    --run-id "your-bee-run-id" \
    --task-filter "Tau2BenchTask" \
    --sample-limit 100 \
    --verbose
```

## Viewer Features

The interactive TUI viewer (`view-bee-samples`) provides:

- **Reward Explanation Tab**: TauBench-specific reward calculation display
- **Rich Formatting**: Markdown rendering with syntax highlighting
- **Token-Aware Display**: Special handling for agentic trajectory tokens
- **JSON Prettification**: Automatic JSON formatting
- **Keyboard Navigation**: Navigate samples without a mouse
- **Multi-Tab View**: Tabs for different data views

### Viewer Keyboard Shortcuts

```
Navigation:
  ←/→     Previous/Next sample
  j/k     Next/Previous sample (Vim-style)
  
Scrolling:
  ↑/↓     Scroll up/down by line
  Shift+↑/↓  Page up/down
  Home/End   Jump to top/bottom

Display:
  m       Toggle markdown mode
  ?       Show help
  q       Quit
```

## Comparing Runs

After running experiments, download and compare results:

```python
import pandas as pd
import json

def load_tau2bench_samples(file_path):
    samples = []
    with open(file_path) as f:
        for line in f:
            data = json.loads(line)
            if data.get('inputs'):
                data['scenario_id'] = data['inputs'].get('scenario_id')
            samples.append(data)
    return pd.DataFrame(samples)

# Load two runs
baseline = load_tau2bench_samples("output/task_Tau2Bench_baseline.jsonl")
experimental = load_tau2bench_samples("output/task_Tau2Bench_v1.jsonl")

# Join on scenario_id
comparison = baseline.merge(experimental, on="scenario_id", suffixes=("_base", "_exp"))

# Compare rewards
comparison["reward_base"] = comparison["metrics_base"].apply(lambda x: x.get("reward", 0))
comparison["reward_exp"] = comparison["metrics_exp"].apply(lambda x: x.get("reward", 0))
comparison["improvement"] = comparison["reward_exp"] - comparison["reward_base"]

print(f"Mean improvement: {comparison['improvement'].mean():.3f}")
```

## Requirements

- Python 3.10+
- `uv` package manager
- Access to cohere-py package registry (for bee)
- API keys for beedb/blobheart as needed
