# Failure Mode Analysis Framework

A framework for performing systematic failure mode analysis on tau2bench evaluation runs using a **two-stage qualitative coding methodology** based on grounded theory.

## Overview

This framework implements a rigorous, data-driven approach to failure analysis:

### Stage 1: Open Coding
**Descriptive analysis of individual samples** - examines each interaction independently to produce rich narrative descriptions without predetermined categories.

### Stage 2: Axial Coding
**Cross-sample pattern analysis** - looks across ALL open codes to identify recurring patterns, create a taxonomy, and assign categorical codes.

This separation ensures that:
- ✅ Categories emerge from data (not predetermined)
- ✅ Rich context is preserved in open coding
- ✅ Patterns are identified through systematic comparison
- ✅ Taxonomy is data-driven and hierarchical

## Architecture

```
failure_analysis/
├── cli/
│   ├── open_coder.py        # Stage 1: Open coding
│   └── axial_coder.py       # Stage 2: Axial coding
├── outputs/                 # Analysis results organized by project
│   └── project_name/
│       ├── original_*.jsonl         # Original bee run
│       ├── open_coded_*.jsonl       # Open coding results
│       ├── axial_coded_*.jsonl      # Axial coding results
│       └── *_taxonomy.json          # Taxonomy
├── logs/                    # Detailed logs of analysis runs
└── README.md               # This file
```

**Note**: All outputs are organized into project folders for clean separation of different analyses.

## Setup

### Prerequisites

1. **OpenAI API Key**: Required for o3 model access
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

2. **Python Dependencies**:
   ```bash
   uv pip install aiohttp tiktoken
   ```

### Data Input

The framework works with JSONL files downloaded from bee runs:
```bash
uv run download-bee-run --run-id <run-id>
```

This produces files like:
```
output/bee_run_<id>_<timestamp>.jsonl
```

## Usage

### Stage 1: Open Coding

Analyze individual samples with descriptive narratives:

```bash
# Analyze all samples (project name is REQUIRED)
python failure_analysis/cli/open_coder.py \
  --input output/bee_run_xyz.jsonl \
  --project my_analysis

# Analyze first N samples
python failure_analysis/cli/open_coder.py \
  --input output/bee_run_xyz.jsonl \
  --project my_analysis \
  --num-samples 10

# Adjust concurrency
python failure_analysis/cli/open_coder.py \
  --input output/bee_run_xyz.jsonl \
  --project my_analysis \
  --num-samples 20 \
  --max-concurrent 30

# Overwrite existing project
python failure_analysis/cli/open_coder.py \
  --input output/bee_run_xyz.jsonl \
  --project my_analysis \
  --overwrite
```

**Output**: 
- `failure_analysis/outputs/{project_name}/original_*.jsonl` - Original bee run (copied)
- `failure_analysis/outputs/{project_name}/open_coded_*.jsonl` - Open coding results

**Note**: `--project` is **required**. Use `--overwrite` to replace existing projects.

### Stage 2: Axial Coding

Analyze patterns across samples and create taxonomy:

```bash
# Run axial coding on open coded results (project name is REQUIRED)
python failure_analysis/cli/axial_coder.py \
  --input failure_analysis/outputs/my_analysis/open_coded_*.jsonl \
  --project my_analysis

# Overwrite existing axial coding results
python failure_analysis/cli/axial_coder.py \
  --input failure_analysis/outputs/my_analysis/open_coded_*.jsonl \
  --project my_analysis \
  --overwrite
```

**Output**: 
- `failure_analysis/outputs/{project_name}/axial_coded_*.jsonl` - Enriched samples with codes
- `failure_analysis/outputs/{project_name}/*_taxonomy.json` - Complete taxonomy with definitions

**Note**: `--project` is **required** and must match an existing project created by open_coder. Use `--overwrite` to replace existing axial results.

## Output Formats

### Open Coding Output

```json
{
  "sample_id": "task_0_run_0",
  "success": false,
  "reward": 0.25,
  "context": {
    "task_name": "...",
    "conversation": [...],
    "tau2bench_rewards": {...}
  },
  "coding": {
    "descriptive_summary": "2-3 sentence summary of what happened",
    "failure_point_turn": 5,
    "detailed_analysis": "Comprehensive narrative analysis...",
    "issues_identified": [
      "Specific issue 1 described in detail",
      "Specific issue 2 described in detail"
    ],
    "observations": "Notable patterns or behaviors...",
    "recommendations": "Specific actionable recommendations..."
  },
  "raw_response": "...",
  "api_usage": {"prompt_tokens": 1500, "completion_tokens": 300}
}
```

### Axial Coding Output

```json
{
  "sample_id": "task_0_run_0",
  "success": false,
  "coding": { /* open coding results */ },
  "axial_coding": {
    "primary_code": "tool_availability_error",
    "secondary_codes": ["lack_of_adaptability"],
    "severity": "major",
    "rationale": "Brief explanation of why these codes were assigned"
  }
}
```

### Taxonomy Output

```json
{
  "primary_categories": [
    {
      "name": "Tool Management Issues",
      "definition": "Issues related to tool availability and usage",
      "subcategories": [
        {
          "code": "tool_availability_error",
          "definition": "Errors from using unavailable tools",
          "indicators": ["Invalid tool name", "Tool not available"],
          "sample_ids": ["sample1", "sample2"]
        }
      ]
    }
  ]
}
```

## Methodology

### Open Coding Best Practices

**Do**:
- ✅ Describe what happened in narrative form
- ✅ Point to specific turn numbers
- ✅ Note patterns and behaviors
- ✅ Provide detailed issue descriptions
- ✅ Generate sample-specific recommendations

**Don't**:
- ❌ Assign categorical labels
- ❌ Force predetermined categories
- ❌ Make cross-sample comparisons
- ❌ Create taxonomies

### Axial Coding Best Practices

**Do**:
- ✅ Read ALL open codes before categorizing
- ✅ Use constant comparison method
- ✅ Let categories emerge from data
- ✅ Create hierarchical taxonomy
- ✅ Define each code clearly
- ✅ Identify indicators for each code
- ✅ Require codes to appear in 2+ samples

**Don't**:
- ❌ Use predetermined categories
- ❌ Create one-off codes
- ❌ Make codes too broad or too narrow
- ❌ Forget to define relationships between codes

## Token Management

### Open Coding
- Includes full conversation for detailed analysis
- ~2000-4000 tokens per sample (typical)
- Processed in parallel batches (default: 3 concurrent)

### Axial Coding
- Uses **compact representations** only (no conversations)
- Typical input: 300-400 tokens per sample
- Single API call for all samples
- Example: 10 samples = ~3,600 tokens input, ~1,500 output

Token counts are logged before and after each API call for transparency.

## Logging

### Log Levels

- **File Log** (`failure_analysis/logs/`): Detailed DEBUG-level logs
- **Console**: INFO-level progress and results

### What's Logged

- Sample processing progress
- API token usage (estimated and actual)
- Parsing successes/errors
- Summary statistics
- Code distributions
- Taxonomy structure

Example log files:
```
failure_analysis/logs/open_coding_20251015_112143.log
failure_analysis/logs/axial_coding_20251015_112409.log
```

## Example Workflow

```bash
# 1. Download bee run
uv run download-bee-run --run-id abc123

# 2. Open coding: Analyze individual samples
export OPENAI_API_KEY="your-key"
python failure_analysis/cli/open_coder.py \
  --input output/bee_run_abc123_*.jsonl \
  --project my_experiment \
  --num-samples 20 \
  --max-concurrent 30

# 3. Axial coding: Identify patterns across samples
python failure_analysis/cli/axial_coder.py \
  --input failure_analysis/outputs/my_experiment/open_coded_*.jsonl \
  --project my_experiment

# 4. Review taxonomy
cat failure_analysis/outputs/my_experiment/*_taxonomy.json | jq .

# 5. Analyze code distribution
jq '.axial_coding.primary_code' \
  failure_analysis/outputs/my_experiment/axial_coded_*.jsonl | \
  sort | uniq -c | sort -rn
```

## Analyzing Results

### Python Analysis

```python
import json
from collections import Counter

# Load axial coded results
results = []
with open('failure_analysis/outputs/axial_coded_results.jsonl') as f:
    for line in f:
        results.append(json.loads(line))

# Count primary codes
primary_codes = Counter(r['axial_coding']['primary_code'] for r in results)
print("Primary Failure Modes:")
for code, count in primary_codes.most_common():
    print(f"  {code:40s}: {count}")

# Analyze by severity
severities = Counter(r['axial_coding']['severity'] for r in results)
print("\nSeverity Distribution:")
for severity, count in severities.items():
    print(f"  {severity:15s}: {count}")

# Load taxonomy
with open('failure_analysis/outputs/taxonomy.json') as f:
    taxonomy = json.load(f)
    
print(f"\nTaxonomy: {len(taxonomy['primary_categories'])} primary categories")
for cat in taxonomy['primary_categories']:
    subcats = len(cat['subcategories'])
    print(f"  • {cat['name']:30s} ({subcats} subcategories)")
```

### Command Line Analysis

```bash
# Count primary codes
jq -r '.axial_coding.primary_code' \
  failure_analysis/outputs/*_axial_coded_*.jsonl | \
  sort | uniq -c | sort -rn

# Extract all critical severity samples
jq 'select(.axial_coding.severity == "critical")' \
  failure_analysis/outputs/*_axial_coded_*.jsonl

# List all samples with tool errors
jq 'select(.axial_coding.primary_code == "tool_availability_error") | .sample_id' \
  failure_analysis/outputs/*_axial_coded_*.jsonl
```

## Model Configuration

- **Model**: OpenAI `o3` (via responses API)
- **Reasoning Effort**: `high` (maximum reasoning capability)
- **Timeout**:
  - Open coding: 60s per sample
  - Axial coding: 600s (allows large dataset analysis)

**Note**: The o3 model via responses API does not support `temperature` or `max_tokens` parameters.

## Context Provided to Model

### Open Coding Context

For each sample, the model receives:
1. **Tau2Bench Background**: What the benchmark tests
2. **Tool Access Model**: agent-side vs user-side tools
3. **Reward Components**: How success is measured
4. **User's Goal**: What the customer wanted to achieve
5. **Conversation Transcript**: Full agent-user interaction (up to 50 turns)
6. **Tool Calls & Results**: All tool invocations and outputs
7. **Reward Details**: Breakdown of scoring

### Axial Coding Context

For taxonomy creation, the model receives:
1. **Open Coding Methodology**: What open coding is and why
2. **ALL Open Coded Samples**: Compact representations (no full conversations)
   - Sample ID, success, reward
   - Descriptive summary
   - Issues identified
   - Observations
3. **Constant Comparison Instructions**: How to compare across samples
4. **Taxonomy Requirements**: Structure, definitions, indicators

## References

- **Grounded Theory**: [Strauss & Corbin](https://en.wikipedia.org/wiki/Grounded_theory)
- **Open Coding**: [Qualitative Research Methods](https://atlasti.com/research-hub/open-coding)
- **Axial Coding**: [Cross-sample Pattern Analysis](https://en.wikipedia.org/wiki/Coding_(social_sciences))
- **Tau2Bench**: Multi-agent simulation benchmark for customer service evaluation

---

**Framework Version**: 2.0 (Two-stage coding with o3 model)  
**Last Updated**: October 15, 2025  
**Status**: ✅ Production ready - All JSON parsing and idempotency issues resolved
