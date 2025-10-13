# Prompt Patches

This directory contains prompt patches that fix specific issues with tau2bench evaluations.

## Structure

Each patch is a text file with an UPPER_CASE_SNAKE_CASE identifier:
- `{PATCH_ID}.txt` - The patch content to append to the system prompt

## Matching Failure Reports

Each patch has a corresponding failure report in `../failures/`:
- `../failures/{PATCH_ID}.md` - Detailed analysis of the issue this patch fixes

## Usage

### In TOML Config:
```toml
[task.Tau2BenchTask.Telecom]
domain = "telecom"
prompt_patches = ["TOOL_CONFUSION_AGENT_VS_USER"]
```

### Via Command Line:
```bash
./experiments/scripts/run-telecom-eval.sh --patches TOOL_CONFUSION_AGENT_VS_USER
```

## Available Patches

### `TOOL_CONFUSION_AGENT_VS_USER`
**Issue**: Model attempts to call user device tools directly  
**Fix**: Clarifies which tools the agent can call vs which tools the user runs  
**Impact**: 91% error reduction, +35% success rate improvement  
**Status**: ✅ Validated

## Adding New Patches

1. Document the failure in `../failures/{NEW_PATCH_ID}.md`
2. Create the patch file: `{NEW_PATCH_ID}.txt`
3. Test with: `./experiments/scripts/run-telecom-eval.sh --patches {NEW_PATCH_ID} --num-tasks 5`
4. Validate improvement before enabling by default
5. Update this README with results

