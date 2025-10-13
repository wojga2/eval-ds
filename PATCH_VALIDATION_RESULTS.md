# Preamble Patch Validation Results

**Run ID**: `11c0bd5b-3667-4f2b-a7e9-66eaf82a5ecf`  
**Date**: October 13, 2025  
**Status**: ⚠️ **PATCH NOT WORKING** - Config loaded but not injected

---

## Executive Summary

The preamble patch **was successfully loaded into the task config** but **was NOT injected into the actual system prompt** seen by the model. As a result, the model behavior did not improve meaningfully, and it continues to attempt calling user-side tools with the `assistant/` prefix.

---

## Results Comparison

| Metric | Before (bee_run_0ac12b3e) | After (bee_run_11c0bd5b) | Change |
|--------|--------------------------|-------------------------|--------|
| Success Rate | 5/20 (25%) | 6/20 (30%) | +5% |
| Average Reward | 0.250 | 0.300 | +0.050 |
| "Invalid tool name" errors | ~18 | ~348 | Much worse! |

### Error Analysis

The model attempted to call these USER tools with `assistant/` prefix:

| Tool | Error Count |
|------|-------------|
| `toggle_data_saver_mode` | 90 |
| `set_network_mode_preference` | 90 |
| `check_network_status` | 38 |
| `run_speed_test` | 28 |
| `check_network_mode_preference` | 22 |
| `check_data_restriction_status` | 14 |
| `reset_apn_settings` | 12 |
| `check_apn_settings` | 10 |
| `toggle_data` | 8 |
| `toggle_roaming` | 6 |
| **Total** | **~348 errors** |

---

## Root Cause Analysis

### What Worked ✅

1. **Config Loading**: The `preamble_patch` field (863 characters) was successfully loaded into the task config
2. **Monkeypatch Applied**: Logs show:
   ```
   ✅ Applied preamble_patch monkeypatch to tau2bench
   ✅ Patched Tau2BenchTask.__init__ for preamble_patch config loading
   ✅ Patched get_chatbot_system_prompt for preamble injection
   ✅ Patched check_unused_options to allow preamble_patch field
   ```
3. **No Validation Errors**: The task ran without "unused options" errors

### What Failed ❌

1. **System Prompt Injection**: The preamble patch content was **NOT present** in the actual system prompt sent to the model
2. **Verification**:
   - Checked first sample's System message
   - No `<preamble_patch>` tags found
   - No CRITICAL instructions found
   - No tool categorization text found

### Why It Failed

The `get_patched_chatbot_system_prompt()` function in `tau2bench_preamble_patch.py` was either:
1. **Not called at all** - `get_chatbot_system_prompt()` may not be invoked during scenario building
2. **Called but ignored** - The return value may not be used in the actual prompt construction
3. **Overwritten** - Another process may be generating the system prompt differently
4. **Wrong scope** - The patch may not persist across process boundaries or multiprocessing

---

## Technical Details

### Config Verification

From the logs, the config contained:

```python
'preamble_patch': '''CRITICAL - Tool Access Clarification:

YOU (the agent) can directly call these tools:
  - get_customer_by_phone, get_customer_by_id, get_details_by_id
  - get_data_usage, enable_roaming, refuel_data
  - transfer_to_human_agents

The CUSTOMER runs these tools on their device:
  - check_network_status, run_speed_test, toggle_airplane_mode
  - check_status_bar, toggle_data, toggle_roaming
  - check_sim_status, check_apn_settings, etc.

When troubleshooting, the policy describes tools the customer can run.
YOU CANNOT call these customer tools directly. Instead:
  1. Guide the customer to run the appropriate tool on their device
  2. Ask them to report the results back to you
  3. Use their feedback to diagnose and solve the issue

Example: Say "Please check your network status and let me know what you see"
NOT: try to call check_network_status() yourself
'''
```

### System Prompt Reality

The actual system prompt seen by the model:

```xml
<instructions>
You are a customer service agent that helps the user according to the <policy> provided below.
In each turn you can either:
- Send a message to the user.
- Make a tool call.
You cannot do both at the same time.

Try to be helpful and always follow the policy. Always make sure you generate valid JSON only.
</instructions>
<policy>
[... telecom policy ...]
</policy>
```

**NO `<preamble_patch>` block present!**

---

## Why Minimal Improvement?

The slight improvement (+1 task, 5%) is likely due to:
- Random variation
- Different task selection/ordering
- Possibly some indirect effect of the config being present

But the core issue remains: **the model never received our clarifying instructions**.

---

## Next Steps

### Option 1: Debug the Monkeypatch
- Add print statements to `get_patched_chatbot_system_prompt()` to verify it's being called
- Check if the function is called during task initialization or scenario building
- Verify the patched function persists across multiprocessing boundaries

### Option 2: Alternative Injection Point
- Find where the actual system prompt is constructed in `comb`
- Patch at a later stage in the pipeline
- Consider patching the scenario builder directly instead of just `get_chatbot_system_prompt()`

### Option 3: Direct Modification
- Temporarily modify `~/dev/apiary/comb/comb/envs/tau2bench/utils/chatbot_system_prompt.py`
- Add the clarifying instructions directly to `CHATBOT_AGENT_INSTRUCTION`
- Verify this approach works before implementing a cleaner solution

### Option 4: Policy File Modification
- The policy is loaded from GCS (`gs://...`)
- Modify the source policy files to include the clarifying instructions
- This would be the most maintainable long-term solution

---

## Conclusion

**Status**: ⚠️ The preamble patch implementation is incomplete.

While the infrastructure for loading and passing the patch is working correctly, the actual injection into the system prompt is not happening. The monkeypatch approach needs debugging or an alternative injection strategy is required.

**Recommendation**: Use Option 3 (direct modification) for immediate validation, then implement Option 4 (policy file modification) as the permanent solution.

---

**Files Referenced**:
- Run data: `output/bee_run_11c0bd5b_20251013_172933.jsonl`
- Run logs: `experiments/logs/tau2bench_telecom_20251013_171955.log`
- Config: `experiments/configs/tau2bench_telecom_focused.toml`
- Patch code: `tau2bench_preamble_patch.py`
- Integration: `experiments/scripts/run_bee_with_patch.py`

