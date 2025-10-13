# Tau2Bench Telecom Tool Confusion - Fix Complete ✅

**Date**: October 13, 2025  
**Status**: FIXED & VALIDATED  
**Fix Location**: `~/dev/apiary/comb/comb/envs/tau2bench/utils/chatbot_system_prompt.py`

---

## Executive Summary

Successfully resolved the critical bug where the chatbot agent was attempting to call user-side device tools directly, causing 90% task failure rates. The fix was implemented directly in the apiary codebase and validated with a 91% error reduction and 140% improvement in success rates.

---

## Results

| Metric | Before Fix | After Fix | Improvement |
|--------|-----------|-----------|-------------|
| **Success Rate** | 5/20 (25%) | 12/20 (60%) | **+140% (+35 pts)** |
| **Average Reward** | 0.250 | 0.600 | **+140%** |
| **Invalid Tool Errors** | 245 | 22 | **-91% reduction** |

### Key Improvements:
- ✅ **7 additional tasks** successfully completed
- ✅ **223 fewer** invalid tool call errors
- ✅ **35 percentage point** increase in success rate

---

## The Problem

The model was misinterpreting the system prompt and attempting to call user device tools (like `check_network_status`, `run_speed_test`, `toggle_airplane_mode`) with the `assistant/` prefix, when these tools should only be run by the customer on their device.

**Root Cause**: Ambiguous preamble text didn't clearly distinguish between:
- **AGENT TOOLS**: Tools the chatbot can call directly
- **USER DEVICE TOOLS**: Tools the customer runs on their device

---

## The Solution

Modified `chatbot_system_prompt.py` to add explicit tool access clarification:

```python
CHATBOT_AGENT_INSTRUCTION = """
... existing instructions ...

CRITICAL - Tool Access Boundaries:

There are TWO types of tools in this system:

AGENT TOOLS (you can call these directly):
  - Customer lookup: get_customer_by_phone, get_customer_by_id, get_details_by_id
  - Account management: get_data_usage, enable_roaming, refuel_data, resume_line, etc.
  - System actions: transfer_to_human_agents, send_payment_request, make_payment, etc.

USER DEVICE TOOLS (the customer runs these on their device):
  - Diagnostic tools: check_network_status, run_speed_test, check_status_bar, check_sim_status, etc.
  - Device actions: toggle_airplane_mode, toggle_data, toggle_roaming, toggle_data_saver_mode, etc.

When the policy describes troubleshooting steps, it's telling you what to GUIDE the customer to do on THEIR device.

You CANNOT call user device tools directly. Instead:
  1. Instruct the customer to run the appropriate tool on their device
  2. Ask them to report the results back to you
  3. Use their feedback to diagnose and solve the issue

Example:
  ✓ CORRECT: "Please check your network status by going to Settings and let me know what you see"
  ✗ WRONG: Attempting to call check_network_status() yourself
""".strip()
```

---

## Implementation Journey

### Attempts (7 iterations over testing cycle):
1. **Monkeypatch approach** (Attempts 1-7): Failed due to multiprocessing issues
   - Worker processes don't inherit patched function references
   - Import timing made it impossible to patch correctly
2. **Direct source modification**: ✅ **SUCCESS**
   - Modified apiary source file directly
   - Clean, maintainable solution
   - Works perfectly with multiprocessing

---

## Files Modified

### Apiary (1 file):
- ✅ `~/dev/apiary/comb/comb/envs/tau2bench/utils/chatbot_system_prompt.py`
  - Added CRITICAL section to `CHATBOT_AGENT_INSTRUCTION`

### Eval-DS (cleaned up):
- ✅ Deleted: `tau2bench_preamble_patch.py` (monkeypatch no longer needed)
- ✅ Deleted: `tau2bench_task_wrapper.py` (wrapper no longer needed)
- ✅ Deleted: `tests/test_preamble_patch.py` (tests no longer needed)
- ✅ Modified: `experiments/scripts/run_bee_with_patch.py` (removed preamble patch code)
- ✅ Modified: `experiments/configs/tau2bench_telecom.toml` (removed `preamble_patch` field)
- ✅ Modified: `experiments/configs/tau2bench_telecom_focused.toml` (removed `preamble_patch` field)

---

## Validation Tests

### Test 1: Single Task (Prompt Verification)
- **Run ID**: `9f348293-7787-4756-b49e-7e85340bf059`
- **Result**: ✅ CRITICAL section present in system prompt
- **Verified**: All key phrases detected in prompt

### Test 2: 20 Tasks (Behavior Validation)
- **Run ID**: `d66cb061-2490-443c-873a-71c9ba2bd922`
- **Result**: ✅ Significant improvement
- **Metrics**:
  - Success: 25% → 60% (+140%)
  - Errors: 245 → 22 (-91%)

---

## Documentation

### Created:
- `experiments/failures/TOOL_CONFUSION_BUG.md` - Comprehensive bug analysis with 5 examples
- `experiments/failures/README.md` - Failure report index
- `PATCH_DEBUG_STATUS.md` - Debugging history (7 iterations)
- `PATCH_VALIDATION_RESULTS.md` - Initial validation results
- `FIX_COMPLETE_SUMMARY.md` - This document

### Archived (for reference):
- Monkeypatch attempts and learnings documented in `PATCH_DEBUG_STATUS.md`

---

## Lessons Learned

1. **Multiprocessing Challenges**: Monkeypatching doesn't work well with Python multiprocessing
   - Function references are copied, not shared
   - Import timing is critical and hard to control

2. **Direct Source Modification**: Sometimes the simplest solution is best
   - Easier to maintain
   - No complex workarounds
   - Works reliably

3. **Prompt Engineering**: Clear, explicit instructions are crucial
   - Models need explicit tool access boundaries
   - Examples help reinforce the correct behavior
   - Structure matters (AGENT TOOLS vs USER DEVICE TOOLS)

4. **Validation is Key**: Always measure impact
   - Single task tests verify the fix is present
   - Multi-task tests validate effectiveness

---

## Next Steps

1. ✅ **COMPLETE**: Fix implemented and validated
2. ⏭️ **Monitor**: Watch for any edge cases in production
3. ⏭️ **Consider**: Upstreaming this fix to tau2bench policy files
4. ⏭️ **Extend**: Apply similar clarifications to other domains (airline, retail) if needed

---

## Command Reference

### Run Evaluation:
```bash
./experiments/scripts/run-telecom-eval.sh --focused --num-tasks 20
```

### Download Results:
```bash
uv run download-bee-run --run-id <run_id>
```

### Analyze Results:
```python
import json
with open('output/bee_run_*.jsonl') as f:
    for line in f:
        data = json.loads(line)
        # Check success rate, errors, etc.
```

---

**Status**: ✅ **FIX COMPLETE & VALIDATED**  
**Impact**: 🎯 **91% error reduction, 140% success improvement**  
**Maintainability**: ✅ **Clean apiary modification, all monkeypatches removed**

