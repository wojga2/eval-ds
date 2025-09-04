# 🐝 Eval DS - Bee Run Data Loader

A comprehensive Python toolkit for discovering, filtering, and analyzing bee run data from Cohere's evaluation system.

## ✨ Features

### 🔍 Bee Run Discovery
- **Unified CLI tool** for finding bee runs by estimator, task, user, or recency
- **Comprehensive filtering** with multiple criteria support
- **Interactive and command-line modes** for different workflows
- **Real-time data** from production and staging environments

### 📊 Data Analysis
- Load bee run information and metadata
- Retrieve all task runs associated with a bee run
- Load samples from specific task runs
- Convert samples to pandas DataFrame for analysis
- Basic data analysis and statistics
- Export data to CSV for further analysis

## 🚀 Installation

This project uses `uv` for dependency management. Make sure you have `uv` installed and access to the Cohere artifact registry.

```bash
# Install dependencies
uv sync

# Or run directly
uv run python -m eval_ds.main
```

## 📖 Usage Guide

### Step 1: Discover Available Bee Run IDs

Use the `bee_search.py` CLI tool to find bee run IDs you can analyze:

#### **Basic Search Commands**
```bash
# Search for Command-R estimators
uv run python bee_search.py --estimator "command-r" --limit 5

# Search for GPT-4 estimators  
uv run python bee_search.py --estimator "gpt-4" --limit 3

# Recent runs
uv run python bee_search.py --recent --limit 10

# Search by task with estimator filter
uv run python bee_search.py --task "hellaswag" --estimator "command-r"
```

#### **Advanced Filtering**
```bash
# Multiple filters - recent runs with specific estimator and task
uv run python bee_search.py --recent --estimator "command-a" --task "IFEval" --limit 5

# Filter by user
uv run python bee_search.py --recent --user "alice" --estimator "gpt" --limit 10

# Get all available tasks and estimators
uv run python bee_search.py --list-tasks
uv run python bee_search.py --list-estimators --limit 20
```

#### **CLI Options Reference**
- `--estimator` / `-e`: Search by estimator pattern
- `--task` / `-t`: Search by task name
- `--user` / `-u`: Filter by wandb user
- `--recent`: Show recent runs
- `--limit` / `-l`: Maximum results (default: 10)
- `--environment`: "production" or "staging" (default: production)
- `--list-tasks`: List all available tasks
- `--list-estimators`: List available estimators
- `--get-run`: Get details for specific bee run ID
- `--verbose` / `-v`: Enable verbose output

#### **Sample Output**
```
📋 Recent runs (estimator: command-a, task: IFEval) (2 found):
====================================================================================================
 1. 🐝 c4d4811b... ✅
     👤 User: ava
     📅 Created: 2025-09-04 10:12:13.182538+00:00
     🤖 Estimator: command-a-03-2025-eval
     📊 Task: AgenticSafetyContentToolTask.V0
     🔗 W&B: https://cohere.wandb.io/cohere/agentic_safety/runs/abc123
     📈 Metrics: recall, precision, num_samples...

💡 Found 2 matching runs!
📝 Copy any bee_run_id above for analysis:
   BEE_RUN_ID = 'c4d4811b-8d3b-4e41-b48a-18983fb41123'
```

### Step 2: Analyze Your Chosen Bee Run

Replace `BEE_RUN_ID` in the main script with a real bee run ID from the discovery tool:

```python
from eval_ds.main import BeeRunLoader
import asyncio

async def load_data():
    loader = BeeRunLoader(environment="production")
    
    # Use a real bee run ID from discovery tool
    bee_run_id = "c4d4811b-8d3b-4e41-b48a-18983fb41123"  
    
    # Load bee run info
    bee_run_info = await loader.load_bee_run_info(bee_run_id)
    
    # Load task runs
    task_runs = await loader.load_task_runs_for_bee_run(bee_run_id)
    
    # Load samples from first task run
    if task_runs:
        samples = await loader.load_samples_for_task_run(task_runs[0]['task_run_id'])
        df = loader.samples_to_dataframe(samples)
        loader.analyze_samples(df)

asyncio.run(load_data())
```

## 🎯 Common Search Patterns

### By Model Family
```bash
# Cohere models
uv run python bee_search.py --estimator "command-r" --limit 10
uv run python bee_search.py --estimator "c4ai" --limit 10

# OpenAI models  
uv run python bee_search.py --estimator "gpt-4" --limit 10
uv run python bee_search.py --estimator "gpt-3.5" --limit 10

# Anthropic models
uv run python bee_search.py --estimator "claude" --limit 10

# Meta models
uv run python bee_search.py --estimator "llama" --limit 10

# Google models
uv run python bee_search.py --estimator "gemini" --limit 10
```

### By Evaluation Task
```bash
# Popular benchmarks
uv run python bee_search.py --task "hellaswag" --limit 10
uv run python bee_search.py --task "mmlu" --limit 10
uv run python bee_search.py --task "gsm8k" --limit 10
uv run python bee_search.py --task "IFEval" --limit 10

# Combined task + estimator search
uv run python bee_search.py --task "hellaswag" --estimator "command-r" --limit 5
```

### By Training Type
```bash
# Instruction-tuned models
uv run python bee_search.py --estimator "instruct" --limit 10

# Chat models
uv run python bee_search.py --estimator "chat" --limit 10

# Base models
uv run python bee_search.py --estimator "base" --limit 10
```

## ⚡ Quick Commands

```bash
# 1. Search for bee runs
uv run python bee_search.py --estimator "command-r" --limit 5
uv run python bee_search.py --recent --user "alice" --limit 10

# 2. Run the main analysis (edit BEE_RUN_ID first!)
uv run python -m eval_ds.main

# 3. Run the example (edit BEE_RUN_ID first!)
uv run python example.py

# 4. Run tests
uv run python -m pytest test_bee_search.py -v
```

## ⚙️ Configuration

The `BeeRunLoader` class accepts several configuration options:

- `environment`: "production" or "staging" (default: "production")
- `use_sa`: Whether to use service account authentication (default: True)
- `verbose`: Enable verbose logging (default: False)

## 📊 Sample Analysis Features

The tool automatically provides:

- 📊 Basic statistics (row count, column count, memory usage)
- 📋 Column type information
- 📈 Metrics summary (for columns starting with 'metric_')
- ❓ Missing data analysis
- 💾 CSV export functionality

## 📝 Example Output

```
🐝 Bee Run Data Loader
==================================================
🔧 Configuration:
  Environment: production
  Sample limit: 100

1️⃣ Loading bee run info for ID: 12345678-1234-1234-1234-123456789abc
✅ Found bee run created at: 2024-01-15 10:30:45.123456+00:00
🔗 W&B URL: https://wandb.ai/cohere/project/runs/run_id

2️⃣ Loading task runs for bee run...
✅ Found 3 task runs:
  1. hellaswag - command-r-plus
  2. mmlu - command-r-plus  
  3. gsm8k - command-r-plus

3️⃣ Loading samples for first task run...
📝 Loading samples from: hellaswag - command-r-plus
✅ Loaded 100 samples

📊 SAMPLE ANALYSIS
==================================================
🔢 Total samples: 100
📋 Columns: 15
```

## 🧪 Testing

Comprehensive test suite with both unit and integration tests:

```bash
# Run all tests
uv run python -m pytest test_bee_search.py -v

# Run only unit tests (fast)
uv run python -m pytest test_bee_search.py -v -k "not integration"

# Run integration tests (slower, requires API access)
uv run python -m pytest test_bee_search.py -v -k "integration"
```

**Test Coverage:**
- ✅ 15 unit tests covering all functionality
- ✅ Multiple filter combinations tested
- ✅ Edge cases and error conditions covered
- ✅ API integration tests with real endpoints

## 📦 Dependencies

- **pandas**: Data manipulation and analysis
- **numpy**: Numerical operations
- **checkpoint-metadata-client**: Cohere's database client
- **hive**: Cohere's evaluation framework
- **pytest**: Testing framework

## 💡 Pro Tips

1. **Start Broad**: Use general patterns like "command-r" then narrow down
2. **Check Status**: Look for ✅ (success) runs for complete data
3. **Recent First**: Results are generally sorted by recency
4. **WandB Links**: Runs with 🔗 links often have richer visualizations
5. **Copy IDs**: Use the provided bee_run_id format for your analysis scripts
6. **Use Filters**: Combine multiple filters for precise results
7. **List First**: Use `--list-tasks` to see available options

## 🚨 Troubleshooting

### Common Issues

**"No runs found"**
- Try broader search patterns (e.g., "command" instead of "command-r-plus")
- Check different tasks with `--task` parameter
- Verify the estimator name exists with `--list-estimators`

**"Slow search"**
- Use smaller `--limit` values
- Try more specific patterns to reduce search space
- The tool searches popular tasks first for faster results

**Authentication Issues**
- Make sure you have access to the Cohere artifact registry
- Check that your service account permissions are correct
- Verify connectivity to the database

**Missing Bee Run**
- Check that the bee run ID exists and you have permissions
- Verify you're using the correct environment (production vs staging)

**Memory Issues**
- Use the `limit` parameter to reduce sample count
- Process data in smaller chunks

## 🏗️ Project Structure

```
eval-ds/
├── bee_search.py          # 🎯 Unified discovery tool (CLI)
├── eval_ds/
│   ├── __init__.py
│   └── main.py           # 📊 Data loading and analysis engine  
├── example.py            # 📝 Usage example
├── test_bee_search.py    # 🧪 Comprehensive test suite
├── pyproject.toml        # ⚙️ Project configuration
└── README.md             # 📖 This documentation
```

## 🤝 Contributing

1. Install dependencies: `uv sync`
2. Make your changes
3. Run tests: `uv run python -m pytest test_bee_search.py -v`
4. Update documentation as needed
5. Test with real examples: `uv run python example.py`

## 📝 Notes

- Requires access to Cohere's internal artifact registry
- Authentication is handled automatically with service accounts
- Data is cached locally for performance
- Large datasets can be limited using the `limit` parameter
- The tool is optimized for common search patterns and popular tasks

---

🎉 **Happy analyzing!** This toolkit makes it easy to discover and analyze bee run data for your evaluation and research needs.