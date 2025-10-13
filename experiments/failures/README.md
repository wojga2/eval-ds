# Tau2Bench Failure Reports

This directory contains detailed analysis of failure modes observed during tau2bench evaluations.

## Purpose

Each failure report documents:
1. **Symptoms**: Specific errors and behavior observed
2. **Examples**: Multiple real cases from evaluation runs
3. **Root Cause**: Technical analysis of why the issue occurs
4. **Impact**: Metrics on how frequently and severely the issue affects evaluations
5. **Solution**: Link to corresponding prompt patch

## Structure

Each report follows the naming convention: `{PATCH_ID}.md`

The corresponding fix is in: `../prompt_patches/{PATCH_ID}.txt`

## Active Failures

### ✅ FIXED - `TOOL_CONFUSION_AGENT_VS_USER`
**Status**: Patched and validated  
**Issue**: Model attempts to call user device tools directly  
**Impact**: 91% error reduction, +35% success rate improvement  
**Patch**: `TOOL_CONFUSION_AGENT_VS_USER.txt`  
**Report**: `TOOL_CONFUSION_AGENT_VS_USER.md`

## Status Legend

- ✅ **FIXED**: Issue resolved with validated patch
- 🔬 **INVESTIGATING**: Root cause analysis in progress
- 📝 **DOCUMENTED**: Issue documented, patch pending
- 🚨 **ACTIVE**: Issue occurring, investigation needed

## Adding New Failure Reports

When you discover a new systematic failure:

1. **Document the failure**:
   - Create `{UPPER_CASE_ID}.md` in this directory
   - Include 3-5 examples from actual runs
   - Quote relevant system prompt sections
   - Analyze root cause
   - Measure impact (error rates, success rates)

2. **Create the patch**:
   - Write fix in `../prompt_patches/{SAME_ID}.txt`
   - Keep patches focused and minimal
   - Reference this report in patch comments

3. **Test the patch**:
   ```bash
   ./experiments/scripts/run-telecom-eval.sh --patches {ID} --num-tasks 10
   ```

4. **Update the TOML** (if validated):
   ```toml
   [task.Tau2BenchTask.Telecom]
   prompt_patches = ["TOOL_CONFUSION_AGENT_VS_USER", "{NEW_ID}"]
   ```

5. **Update this README**:
   - Add to "Active Failures" section
   - Update status as progress is made

## Best Practices

- **Be specific**: Include task IDs and run IDs for reproducibility
- **Show examples**: Quote actual model outputs, not hypotheticals
- **Measure impact**: Before and after metrics validate the fix
- **Stay focused**: One failure mode per report
- **Link patches**: Always connect reports to their fixes

## Architecture Notes

This failure tracking system is part of the eval-ds prompt patching architecture:

```
experiments/
├── failures/          ← Failure documentation (this directory)
│   ├── README.md      ← You are here
│   └── {ID}.md        ← Detailed failure analysis
└── prompt_patches/    ← Prompt fixes
    ├── README.md      ← Patch usage guide  
    └── {ID}.txt       ← Minimal fix for specific failure
```

The patches are loaded via `prompt_patch_loader.py` and injected into the tau2bench system prompt via `run_bee_with_patch.py`.
