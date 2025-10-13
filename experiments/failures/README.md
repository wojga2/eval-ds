# Failure Reports

This directory contains detailed failure analysis reports for tau2bench and other evaluation tasks.

## Reports

### Tau2Bench Telecom Tool Confusion (October 13, 2025)

**Status**: ✅ FIXED - Monkeypatch Solution Implemented & Integrated

**`TOOL_CONFUSION_BUG.md`** - Comprehensive analysis of critical bug where the chatbot attempted to call user device tools directly instead of instructing customers to run them

Key contents:
- Executive summary with impact metrics (245 errors, 90% failure rate)
- Detailed explanation of the problematic preamble and how it's misinterpreted
- 5 real-world examples from logs showing different tool types and contexts
- Pattern analysis demonstrating cascading failure behavior
- Tool architecture explanation (assistant/ vs user/ prefix system)
- Complete fix documentation with before/after comparison
- Lessons learned for prompt engineering, eval design, and multi-agent systems

**Impact**: 18/20 samples (90%) failing with invalid tool call errors

**Root Cause**: Ambiguous preamble text - "you will have to help the customer perform series of actions" was interpreted as "I can call these tools directly" instead of "I should instruct the customer to run these tools"

**Fix**: Updated preambles in all tau2bench telecom configs to explicitly clarify which tools the chatbot can call vs. which tools the customer runs on their device

**Configuration Files Updated**:
- `experiments/configs/tau2bench_telecom.toml` - now includes `preamble_patch` field
- `experiments/configs/tau2bench_telecom_focused.toml` - now includes `preamble_patch` field

**Monkeypatch Solution**:
- `tau2bench_preamble_patch.py` - Core monkeypatch that intercepts `get_chatbot_system_prompt()`
- `tau2bench_task_wrapper.py` - Config loader (reference implementation)
- `experiments/scripts/run_bee_with_patch.py` - **Integrated** - automatically applies patches
- `tests/test_preamble_patch.py` - Unit tests (8/8 passing)

**How It Works**:
The `run_bee_with_patch.py` script now automatically:
1. Patches `get_chatbot_system_prompt()` to inject preamble content
2. Patches `Tau2BenchTask.__init__` to load `preamble_patch` from config
3. Injects the patch between `</instructions>` and `<policy>` tags

**Zero modifications to apiary codebase required!**

See `MONKEYPATCH_SOLUTION.md` for detailed implementation and `ROOT_CAUSE_ANALYSIS.md` for architectural background.

---

## Guidelines for Adding New Reports

When documenting a new failure:

1. **Create a descriptive filename**: `[TASK]_[ISSUE_TYPE]_[DATE].md`
2. **Include these sections**:
   - Executive summary with impact metrics
   - Root cause analysis (eval issue vs. model behavior)
   - Real examples from logs with conversation excerpts
   - Pattern analysis showing why the issue occurs
   - The fix or mitigation strategy
   - Validation plan
   - Lessons learned

3. **Link related files**:
   - Original log files
   - Configuration files
   - Code changes

4. **Update this README** with a summary entry

---

## Archive

As issues are resolved and validated, move reports to `experiments/failures/archive/` with a final status update.

