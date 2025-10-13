# Local MCP Solution for Tau2Bench

**Status**: ✅ Working

## Overview

This solution enables running Tau2Bench evaluations locally using:
- Local apiary checkout for bee
- Staging Cohere API (`CO_API_KEY_STAGING`)
- Local MCP servers on ports 8100-8102
- BeeDB for result storage
- **NO modifications to ~/dev/apiary**

## How It Works

### 1. Monkeypatch via Python Wrapper

Instead of config options (not available) or sitecustomize.py (environment issues), we use a Python wrapper script that:
1. Runs within `uv run` environment
2. Imports tau2bench modules
3. Patches `Tau2BenchTask.run_estimator()` to override `tool_env_per_domain` in the scenario config
4. Calls bee's main()

**Key file**: `experiments/scripts/run_bee_with_patch.py`

### 2. MCP Server Configuration

The patch overrides the default MCP server URLs with local ones:

```python
local_tool_env = {
    "airline": {
        "type": "http",
        "name": "airline",
        "server_uri": "http://127.0.0.1:8100/mcp",  # ← /mcp path is critical
        "version": "local",
    },
    "retail": {...},
    "telecom": {...},
}

scenario_config = scenario_config.model_copy(
    update={
        "tool_env_per_domain": local_tool_env,  # ← Override here
        ...
    }
)
```

### 3. Why This Works

- **No apiary changes**: All patching happens in eval-ds repository
- **Right timing**: Patch applies after imports but before execution
- **Config override**: Uses pydantic's `model_copy(update={...})` which is the official way to override scenario config
- **Correct endpoint**: MCP servers need `/mcp` path, not just the base URL

## Usage

```bash
# 1. Start MCP servers
./experiments/scripts/manage-mcp-servers.sh start

# 2. Run evaluation
./experiments/scripts/run-telecom-eval.sh --quick

# 3. Stop MCP servers (optional)
./experiments/scripts/manage-mcp-servers.sh stop
```

## Files

- `experiments/scripts/run_bee_with_patch.py` - Python wrapper that patches tau2bench
- `experiments/scripts/run-bee` - Bash wrapper that calls the Python wrapper
- `experiments/scripts/manage-mcp-servers.sh` - MCP server management
- `experiments/scripts/sitecustomize.py` - Unused (kept for reference)

## Key Insights

1. **Config options don't work**: `tool_env_per_domain` is a scenario config field, not a task config field. It can't be set via TOML.

2. **PYTHONSTARTUP doesn't work**: The module isn't imported yet when PYTHONSTARTUP runs.

3. **sitecustomize.py location matters**: Must be in Python's sys.path, but `uv run` uses isolated environments.

4. **Python wrapper is reliable**: Running as a Python script within `uv run` ensures the patch applies at the right time.

5. **MCP endpoint matters**: Servers need `/mcp` path appended to the URL.

## Verification

Successful connection shows:
```
✅ Patched Tau2BenchTask to use local MCP servers:
   - airline:  http://127.0.0.1:8100/mcp
   - retail:   http://127.0.0.1:8101/mcp
   - telecom:  http://127.0.0.1:8102/mcp

...
2025-10-13 13:52:28,030 - mcp.client.streamable_http - INFO - Received session ID: 5c2994dfbc434f40a3fe78468af06c49
2025-10-13 13:52:28,030 - mcp.client.streamable_http - INFO - Negotiated protocol version: 2025-06-18
```

MCP server logs show successful connections:
```
INFO:     127.0.0.1:43022 - "POST /mcp HTTP/1.1" 200 OK
```

## Alternatives Explored

1. ❌ **Config-based**: `tool_env_per_domain` in TOML → "unused task options" error
2. ❌ **PYTHONSTARTUP**: Too early, modules not loaded yet
3. ❌ **sitecustomize.py via PYTHONPATH**: `uv run` isolation issues
4. ✅ **Python wrapper**: Works reliably

## Future Improvements

- Environment variables for MCP server ports (if needed for flexibility)
- Automatic detection of which MCP servers are running
- Support for remote MCP servers via environment variable

