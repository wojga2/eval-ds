# Bee Run Data Tools

Tools for downloading and viewing bee run samples with full metadata and agentic trajectories.

## Quick Start

```bash
# 1. Download samples from a bee run
uv run download-bee-run --run-id "your-bee-run-id"

# 2. View samples in an interactive TUI
uv run view-bee-samples output/task_*.jsonl
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
    --task-filter "BFCLTask" \
    --sample-limit 100 \
    --verbose
```

## Viewer Features

The interactive TUI viewer (`view-bee-samples`) provides:

- **Rich Formatting**: Automatic markdown rendering with syntax highlighting
- **Token-Aware Display**: Special handling for agentic trajectory tokens:
  - 🔧 **SYSTEM** sections (blue)
  - 👤 **USER** sections (green)
  - 🤖 **ASSISTANT** sections (cyan)
  - 💭 **THINKING** sections (yellow)
  - ⚡ **ACTION** sections (magenta)
  - 💬 **RESPONSE** sections (cyan)
  - 🔨 **TOOL RESULT** sections (red)
- **JSON Prettification**: Automatically detects and formats JSON in any field
- **Keyboard Navigation**: Navigate samples and scroll content without a mouse
- **Multi-Tab View**: Separate tabs for Outputs, Inputs, Metrics, Debug Info

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

## What It Downloads

The tool fetches ALL available fields from the checkpoint-tracker API:
- ✅ Sample metadata (IDs, timestamps, hashes)
- ✅ Outputs (raw_prompt, parse info, debug data)
- ✅ Metrics (task evaluation results)
- ✅ Debug info (timing, usage, errors)

## Known Issue: Missing Model Generations

**For BFCL Task:** The `outputs.generations` field is NULL because the BFCL task has a bug where it doesn't save model responses to the database. The download tool correctly fetches all available data - the problem is upstream in the task code.

What you'll see:
```
📊 Output fields: generations=0/3046, raw_generations=0/3046, thinking=0/3046, raw_prompt=3046/3046
⚠️  WARNING: Model generations are NULL but prompts exist.
```

This means:
- ✅ You have the input prompts
- ✅ You have the metrics and pass/fail results
- ❌ Model responses were never saved to the database

## Available Options

```
--run-id          Bee run ID to download
--output-dir      Output directory (default: ./output)
--task-filter     Filter tasks by name (substring match)
--metric-filter   Filter tasks by metric name
--task-run-id     Download specific task run ID
--max-tasks       Limit number of tasks
--sample-limit    Limit samples per task
--verbose         Show detailed progress
```

## Output Format

Saves to JSONL files with one sample per line:
```json
{
  "sample_id": "uuid",
  "task_run_id": "uuid",
  "task_name": "TaskName",
  "outputs": {
    "raw_prompt": "...",
    "generations": null,
    "metrics": {...}
  },
  "metrics": {...},
  "debug_info": {...}
}
```
