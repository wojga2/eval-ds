# Preamble Patch Debugging Status

**Date**: October 13, 2025  
**Attempts**: 7 iterations  
**Status**: ❌ NOT WORKING - Multiprocessing issue

---

## Problem

The preamble patch monkeypatch approach is failing due to multiprocessing. Worker processes don't inherit the patched function references from the main process.

## What We Tried

### Attempt 1-2: Patch in main process
- ❌ Patched `get_chatbot_system_prompt()` in main process
- Result: Function never called (runs in worker processes)

### Attempt 3-4: Patch in `run_estimator()`
- ❌ Applied patch inside `Tau2BenchTask.run_estimator()` (worker process)
- ❌ Patched `builder.get_chatbot_system_prompt`
- Result: Builder module already imported function with `from ... import`

### Attempt 5-7: Patch utils module directly
- ❌ Patched `comb.envs.tau2bench.utils.chatbot_system_prompt.get_chatbot_system_prompt`
- Result: Still not being called - import already happened before patch

## Root Cause

**Import Timing Issue**: The `builder` module imports the function like this:
```python
from comb.envs.tau2bench.utils.chatbot_system_prompt import get_chatbot_system_prompt
```

This creates a local reference. When we patch the module later, the builder's local reference doesn't update.

**Multiprocessing**: Even if we patch early, worker processes are forked/spawned AFTER the import, and they don't see our patches.

---

## Recommended Solution

### Option A: Direct Modification (Fast Validation)

Temporarily modify the source file to validate the fix works:

```bash
# Edit the source directly
vi ~/dev/apiary/comb/comb/envs/tau2bench/utils/chatbot_system_prompt.py
```

Add the clarifying instructions directly to `CHATBOT_AGENT_INSTRUCTION`:

```python
CHATBOT_AGENT_INSTRUCTION = """
You are a customer service agent that helps the user according to the <policy> provided below.
...

CRITICAL - Tool Access Clarification:

YOU (the agent) can directly call these tools:
  - get_customer_by_phone, get_customer_by_id, get_details_by_id
  - get_data_usage, enable_roaming, refuel_data
  - transfer_to_human_agents

The CUSTOMER runs these tools on their device:
  - check_network_status, run_speed_test, toggle_airplane_mode
  - check_status_bar, toggle_data, toggle_roaming
  - check_sim_status, check_apn_settings, etc.

When troubleshooting, YOU CANNOT call these customer tools directly. Instead:
  1. Guide the customer to run the appropriate tool on their device
  2. Ask them to report the results back to you
  3. Use their feedback to diagnose and solve the issue

Example: Say "Please check your network status and let me know what you see"
NOT: try to call check_network_status() yourself
"""
```

**Pros**:
- Will definitely work
- Can validate fix effectiveness immediately
- Simple and clear

**Cons**:
- Modifies apiary code
- Not maintainable long-term
- Will be lost on code updates

### Option B: Policy File Modification (Proper Fix)

Modify the GCS policy files that tau2bench loads:

```bash
# Find the policy files
gsutil ls gs://cohere-dev-central-2/omar_cohere_com/comb/dev/tau2-bench/domains/telecom/

# Download, modify, and re-upload
```

Add clarifying instructions to the telecom policy itself.

**Pros**:
- Maintainable
- No code changes
- Policy-driven

**Cons**:
- Requires GCS access
- Affects all users of that policy
- Slower iteration

### Option C: Patch at Import Time (Complex)

Use import hooks to intercept the module import and patch before `builder` imports it:

```python
import sys
import importlib.abc
import importlib.machinery

class PreamblePatchLoader(importlib.abc.Loader):
    def exec_module(self, module):
        # Patch the module as it's being loaded
        pass
```

**Pros**:
- Clean monkeypatch
- No source modifications

**Cons**:
- Very complex
- Fragile
- Hard to debug

---

## Recommendation

**Use Option A for immediate validation**, then implement Option B as the permanent solution.

1. Directly modify `chatbot_system_prompt.py` to add the clarifying instructions
2. Run evaluation to verify the fix works
3. If successful, work with apiary team to add this to the policy files (Option B)

---

## Test Commands

```bash
# Test with direct modification
./experiments/scripts/run-telecom-eval.sh --focused --num-tasks 20

# Download and analyze
uv run download-bee-run --run-id <run_id>

# Check for improvement
python3 << 'EOF'
import json
with open('output/bee_run_*.jsonl') as f:
    for line in f:
        data = json.loads(line)
        # Check for invalid tool calls
        ...
EOF
```

---

## Next Steps

1. ✅ Document current status (this file)
2. ⚠️  Choose approach (recommend Option A)
3. ⏭️ Implement chosen solution
4. ⏭️ Run validation
5. ⏭️ Measure improvement
6. ⏭️ Implement permanent fix (Option B)

