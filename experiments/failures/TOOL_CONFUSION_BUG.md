# Tau2Bench Telecom: Tool Confusion Bug - Complete Analysis

**Date**: October 13, 2025  
**Severity**: HIGH  
**Impact**: 90% task failure rate (18/20 samples), 245 invalid tool calls  
**Root Cause**: Ambiguous preamble causing model to call user device tools directly  
**Status**: ✅ FIXED

---

## Executive Summary

The tau2bench telecom evaluation experienced **massive failure rates** (18/20 samples = 90%) due to the chatbot attempting to call user device tools (like `check_network_status`, `run_speed_test`, `toggle_airplane_mode`) which it doesn't have access to. This resulted in 245 "Invalid tool name" errors across just 20 samples.

**This is an EVAL ISSUE, not a model misbehavior.** The model was correctly following the instructions in its system prompt, but those instructions were ambiguous about which tools it could call vs. which tools the customer should run.

The chatbot repeatedly tries to execute diagnostic and fix actions on the customer's device remotely, when it should be **instructing the customer** to perform these actions and then using their feedback to troubleshoot. This fundamental misunderstanding led to cascading failures and premature transfers to human agents.

---

## The Problematic Preamble

### What the System Prompt Says

The system prompt includes this technical support policy section that describes user device tools:

```markdown
# What the user can do on their device
Here are the actions a user is able to take on their device.
You must understand those well since as part of technical support 
you will have to help the customer perform series of actions

## Diagnostic Actions (Read-only)
1. **check_status_bar** - Shows what icons are currently visible in your phone's 
   status bar (the area at the top of the screen).
2. **check_network_status** - Checks your phone's connection status to cellular 
   networks and Wi-Fi. Shows airplane mode status, signal strength, network type...
3. **check_network_mode_preference** - Checks your phone's network mode preference...
...
13. **run_speed_test** - Measures your current internet connection speed 
    (download speed). Provides information about connection quality...

## Fix Actions (Write/Modify)
1. **set_network_mode_preference** - Changes the type of cellular network your 
   phone prefers to connect to (e.g., 5G, 4G, 3G).
2. **toggle_airplane_mode** - Turns Airplane Mode ON or OFF. When ON, it 
   disconnects all wireless communications...
3. **reseat_sim_card** - Simulates removing and reinserting your SIM card...
4. **toggle_data** - Turns your phone's mobile data connection ON or OFF...
```

### The Critical Ambiguity

The phrase **"You must understand those well since as part of technical support you will have to help the customer perform series of actions"** creates confusion:

- ✅ **Intended meaning**: "You need to know what these tools do so you can **instruct the customer** to use them"
- ❌ **Model interpretation**: "I will have to **perform these actions** myself as part of technical support"

The model sees:
1. A list of tools with detailed function-like descriptions
2. Instructions saying "you will have to help the customer perform series of actions"
3. Troubleshooting sections using callable syntax like "`run_speed_test()` can be used to check..."
4. Parameter descriptions suggesting these are real function calls

This leads the model to conclude: **"I should call these tools directly to diagnose and fix issues."**

Additionally, the troubleshooting sections use conditional language like:

> If `check_network_status()` shows mobile data is disabled, guide the user to use `toggle_data()` to turn mobile data ON.

The model interprets this as: "First I call `check_network_status()`, then based on the result, I call `toggle_data()`"

---

## Tool Architecture: The Underlying System

Tau2bench uses a prefix-based tool routing system:

### **Assistant Tools** (prefix: `assistant/`)
- **CAN be called directly by the chatbot**
- Examples:
  - `get_customer_by_phone` - Look up customer by phone number
  - `get_customer_by_id` - Look up customer by ID
  - `get_details_by_id` - Get line/plan details
  - `get_data_usage` - Check data consumption
  - `enable_roaming` - Enable roaming for a line
  - `refuel_data` - Add data to a plan
  - `transfer_to_human_agents` - Escalate to human support
- **Successfully called in logs** ✅

### **User Tools** (prefix: `user/`)
- **Should be run BY THE CUSTOMER on their device**
- **The chatbot should INSTRUCT, not EXECUTE**
- Examples:
  - `check_network_status` - Check phone's network connection
  - `run_speed_test` - Test internet speed
  - `toggle_airplane_mode` - Turn airplane mode on/off
  - `check_status_bar` - View status bar icons
  - `toggle_data` - Turn mobile data on/off
  - `check_sim_status` - Check SIM card status
- **When chatbot tries to call them**, system adds `assistant/` prefix → tool not found ❌

---

## Real-World Examples

### Example 1: `check_network_status` - First Diagnostic Attempt

**Sample**: `c0316129-60a5-4ba5-b70f-bb05bf221d1e`

#### User Request
```
Hi there! I'm having trouble with my mobile data—it's either not working 
at all or it's extremely slow. I really need to get excellent internet 
speed on my phone, since I use it for both work and personal stuff. 
Can you help me fix this? I don't have access to Wi-Fi, so I need my 
mobile data to work perfectly.
```

#### Model's Reasoning
```
Alright, let me figure out how to help the user with their mobile data 
issue. The user mentioned their mobile data isn't working or is too slow, 
and they need excellent speed for work and personal use without Wi-Fi.

First, according to the tech support policy, I need to diagnose the 
problem step by step. The user can't access Wi-Fi, so mobile data is 
crucial. The first thing to check is their network status. I should use 
the check_network_status tool to see if there's a signal, data enabled, 
and roaming status. If there's no signal, maybe Airplane Mode is on, 
or the SIM is an issue. If data is disabled, toggling it might help.

Next, if the network status looks okay, I should check the data...
```

#### Tool Call Attempted
```json
{
  "name": "check_network_status",
  "parameters": {}
}
```

#### Error Result
```
Invalid tool name, tool assistant/check_network_status not available.
```

#### Why This Happened

The policy states:

> ## Diagnosing Mobile Data Issues
> `run_speed_test()` can be used to check for potential issues with mobile data.
> ...
> ## Troubleshooting Mobile Data Problems
> ### Mobile Data Disabled
> If `check_network_status()` shows mobile data is disabled, guide the user 
> to use `toggle_data()` to turn mobile data ON.

The model reads this as a workflow:
1. "I call `check_network_status()`"
2. "Based on the result, I guide the user"

**What it should have done**: 
"Could you please check your network status on your phone and let me know what it shows? Specifically, I need to know if mobile data is enabled and what your signal strength is."

---

### Example 2: `check_data_restriction_status` - Alternative Diagnostic

**Sample**: `8a070a17-2a4d-43b2-b7ff-adc07e2d8f02`

#### User Request
```
Hi there! I'm having trouble with my mobile data while I'm abroad in France. 
The internet on my phone is either not working at all or it's extremely slow. 
I really need to get excellent internet speed on my phone—nothing less will do. 
Can you help me fix this?
```

#### Model's Reasoning
```
The user is experiencing mobile data issues in France, needing excellent 
speed. First, I attempted to use the `check_network_status` tool to diagnose 
the problem, but it returned an "Invalid tool name" error. This suggests the 
tool might not be available or there's a system error.

Next steps: Since the primary diagnostic tool failed, I need to proceed with 
alternative tools to gather necessary information. The user's issue involves 
roaming and data connectivity, so I should check roaming status, data 
restrictions, and network mode preferences.

I'll start by checking if data roaming is enabled using `check_network_status` 
again, but since that failed, perhaps try `check_data_restriction_status`...
```

#### Tool Call Attempted
```json
{
  "name": "check_data_restriction_status",
  "parameters": {}
}
```

#### Error Result
```
Invalid tool name, tool assistant/check_data_restriction_status not available.
```

#### Why This Happened

After the first tool fails, the model tries **alternative diagnostic tools** mentioned in the policy. It's following a logical troubleshooting path, but still making the same fundamental error—trying to call user device tools directly.

The policy mentions:

> ### Data Saver Mode
> Data Saver mode is a feature that restricts background data usage and can 
> affect data speeds. If `check_data_restriction_status()` shows "Data Saver 
> mode is ON", guide the user to use `toggle_data_saver_mode()` to turn it OFF.

**What it should have done**: 
"Since you're in France, let's check a few things. First, can you verify if Data Saver mode is turned on in your phone's settings?"

---

### Example 3: `run_speed_test` - Performance Validation

**Sample**: `2e9c4e5d-c90a-4d65-8477-11f2920c8c41`

#### User Request
```
I've restarted my device as you suggested. What should I do next to 
make sure my internet speed is excellent?
```

#### Model's Reasoning
```
Alright, the user has restarted their device and wants to ensure their 
internet speed is excellent. Let me check the tools again. Previously, 
when trying to use check_network_status and check_status_bar, I got errors 
saying the tools weren't available. That suggests those tools might not be 
accessible here.

Looking back at the tech support policy, the available diagnostic tools 
include check_network_status, check_status_bar, and others. But since those 
aren't working, maybe I need to use alternative methods. The policy also 
mentions running a speed test with run_speed_test. That tool is available 
and can measure download speed, which would help determine if the speed is 
excellent.
```

#### Tool Call Attempted
```json
{
  "name": "run_speed_test",
  "parameters": {
    "customer_id": "C1001",
    "line_id": "L1002"
  }
}
```

#### Error Result
```
Invalid tool name, tool assistant/run_speed_test not available.
```

#### Why This Happened

The policy explicitly describes:

> ## Diagnostic Actions (Read-only)
> 13. **run_speed_test** - Measures your current internet connection speed 
>     (download speed). Provides information about connection quality and 
>     what activities it can support. Download speed can be "unknown", 
>     "very poor", "poor", "fair", "good", or "excellent".

Note that the model adds `customer_id` and `line_id` parameters, showing it believes it can **remotely execute a speed test on the specific customer's device**. This reveals the model's mental model: "I can target this user's device and run diagnostics on it."

**What it should have done**: 
"Great! Now let's verify the speed. Please run a speed test on your phone using the built-in test feature and tell me what result you get—specifically whether it shows poor, fair, good, or excellent speed."

---

### Example 4: `toggle_data` - Attempting Remote Fixes

**Sample**: `2e9c4e5d-c90a-4d65-8477-11f2920c8c41`

#### User Request
```
I just restarted my device. My status bar shows excellent signal strength 
and 5G, but it looks like mobile data is currently disabled. What should 
I do next?
```

#### Model's Reasoning
```
Alright, the user has restarted their device, and the status bar shows 
excellent signal strength with 5G, but mobile data is disabled. Let me 
figure out the next steps.

First, I need to confirm the mobile data status. The user mentioned it's 
disabled, so the immediate action is to toggle mobile data back on. 
According to the tech support policy, the tool `toggle_data` can turn 
mobile data on or off. Since it's currently off, I should use this tool 
to enable it.

Additionally, I should check if Data Saver mode is active, as that could 
restrict data usage even when mobile data is on...
```

#### Tool Call Attempted
```json
{
  "name": "toggle_data",
  "parameters": {
    "customer_id": "C1001",
    "line_id": "L1002"
  }
}
```

#### Error Result
```
Invalid tool name, tool assistant/toggle_data not available.
```

#### Why This Happened

Here the user **explicitly states** mobile data is disabled, providing the diagnostic information the model needs. Instead of instructing the user to enable it, the model tries to **remotely toggle it** using the `toggle_data` tool with targeting parameters.

The policy states:

> ## Fix Actions (Write/Modify)
> 4. **toggle_data** - Turns your phone's mobile data connection ON or OFF. 
>    Controls whether your phone can use cellular data for internet access 
>    when Wi-Fi is unavailable.

And in troubleshooting:

> If `check_network_status()` shows mobile data is disabled, guide the user 
> to use `toggle_data()` to turn mobile data ON.

The model reads "guide the user to use `toggle_data()`" but tries to execute it itself rather than guiding.

**What it should have done**: 
"I can see mobile data is disabled. Please enable mobile data in your phone's settings, and then check if your internet starts working."

---

### Example 5: `toggle_airplane_mode` - Escalating to Remote Control

**Sample**: `7513817e-3940-4244-8549-a3ac60abef36`

#### User Request
```
My phone number is 555-123-2002.
```

#### Model's Reasoning (After Multiple Failed Attempts)
```
Okay, let me figure out what to do next. The user is having mobile data 
issues, and I need to help them get excellent speed. First, I recall the 
steps from the tech support policy. I already retrieved the customer's 
details using their phone number. They have three lines: L1001, L1002, 
and L1003. The line matching their phone number is L1002, which is active 
with 8.7GB used out of 15GB. Their plan allows 15GB, so they haven't 
exceeded it yet.

I tried checking the network mode preference, network status, and data 
restriction status, but those tools returned errors saying they're not 
available. That's a problem because those are key diagnostic steps. 
According to the policy, the next step is...
```

#### Tool Call Attempted
```json
{
  "name": "toggle_airplane_mode",
  "parameters": {
    "action": "cycle",
    "customer_id": "C1001",
    "line_id": "L1002"
  }
}
```

#### Error Result
```
Invalid tool name, tool assistant/toggle_airplane_mode not available.
```

#### Why This Happened

After **multiple diagnostic tools fail**, the model escalates to trying **fix actions**. It's particularly noteworthy that it includes:
- `action`: `"cycle"` - suggesting it wants to turn airplane mode off then on
- `customer_id` and `line_id` - targeting the specific device

The policy describes:

> ## Fix Actions (Write/Modify)
> 2. **toggle_airplane_mode** - Turns Airplane Mode ON or OFF. When ON, it 
>    disconnects all wireless communications including cellular, Wi-Fi, 
>    and Bluetooth.

And:

> ### Airplane Mode
> If it is ON, guide the user to use `toggle_airplane_mode()` to turn it OFF.

The model, frustrated by failed diagnostics, attempts to **directly fix** what it hypothesizes is the problem.

**What it should have done**: 
"Let's try some basic troubleshooting. Can you check if Airplane Mode is turned on? If it is, please turn it off and let me know if that helps."

---

## Pattern Analysis

### Common Thread Across All Examples

In every case, the model follows this pattern:

1. **Reads the technical support policy** describing user device tools in detail
2. **Interprets function-call syntax** (`tool_name()`) as actual callable functions
3. **Adds targeting parameters** (`customer_id`, `line_id`) to specify which device to control
4. **Attempts direct execution** instead of instructing the customer
5. **Receives "Invalid tool name" error** when the system adds `assistant/` prefix
6. **Tries alternative tools** following the same flawed approach

### The Cascade Effect

The bug creates a multi-stage failure cascade:

```
Stage 1: Initial Diagnostic Failure
├─ Model tries check_network_status() → Error
├─ Model tries check_status_bar() → Error
└─ Model tries check_data_restriction_status() → Error

Stage 2: Alternative Diagnostics
├─ Model tries check_network_mode_preference() → Error
├─ Model tries run_speed_test() → Error
└─ Model tries check_sim_status() → Error

Stage 3: Attempted Fixes
├─ Model tries toggle_airplane_mode() → Error
├─ Model tries toggle_data() → Error
└─ Model tries reset_apn_settings() → Error

Stage 4: Abandonment
└─ Model calls transfer_to_human_agents() → Success
    └─ Task ends without resolution
```

**Result**: 90% of tasks end in premature transfer, even though many are simple problems (like "enable mobile data" or "turn off airplane mode") that could have been solved with proper instructions to the customer.

### Why This Reveals Correct Model Behavior

The model is actually demonstrating **good troubleshooting logic**:

1. ✅ Follows a systematic diagnostic approach
2. ✅ Tries primary tools first, then alternatives
3. ✅ Moves from diagnosis to fixes when diagnostics "fail"
4. ✅ Escalates to human agents when "all available options exhausted"
5. ✅ Adds appropriate parameters to target specific devices

The problem is NOT the logic—it's the **fundamental misunderstanding** about which tools it has access to.

---

## Impact Statistics

From log file: `output/bee_run_0ac12b3e_20251013_161135.jsonl`

### High-Level Metrics
- **Samples with errors**: 18 out of 20 (90%)
- **Total invalid tool calls**: 245
- **Average errors per failing sample**: 13.6
- **Tasks successfully completed**: 2 out of 20 (10%)

### Most Commonly Attempted Invalid Tools

| Tool Name | Error Count | % of Total | Category |
|-----------|-------------|------------|----------|
| `check_apn_settings` | 48 | 19.6% | Diagnostic |
| `check_sim_status` | 45 | 18.4% | Diagnostic |
| `toggle_data` | 22 | 9.0% | Fix Action |
| `toggle_data_saver_mode` | 21 | 8.6% | Fix Action |
| `toggle_airplane_mode` | 19 | 7.8% | Fix Action |
| `check_network_status` | 18 | 7.3% | Diagnostic |
| `toggle_roaming` | 18 | 7.3% | Fix Action |
| `run_speed_test` | 9 | 3.7% | Diagnostic |
| `check_data_restriction_status` | 8 | 3.3% | Diagnostic |
| `check_network_mode_preference` | 7 | 2.9% | Diagnostic |
| Others | 30 | 12.2% | Mixed |
| **TOTAL** | **245** | **100%** | - |

### Tool Category Breakdown
- **Diagnostic tools**: 60.8% of errors
- **Fix actions**: 39.2% of errors

This shows the model primarily attempts diagnostics first (correct approach), then moves to fixes when diagnostics "fail."

---

## The Fix

### What Changed

Updated the `chat_preamble` in all tau2bench telecom configuration files to explicitly clarify tool boundaries:

```toml
chat_preamble = """
You are an expert customer service agent for a telecommunications company.
You excel at carefully following instructions and using the available tools precisely.

When handling customer requests:
1. Always verify customer identity first using YOUR available lookup tools 
   (get_customer_by_phone, get_customer_by_id, etc.)
2. Carefully read all account and service details before taking action
3. Confirm with the customer before making any changes to their account
4. Use the minimum number of tool calls needed to complete the task efficiently
5. Pay special attention to billing, plan changes, and technical support issues

IMPORTANT - Understanding Tool Access:
- YOU can directly call: get_customer_by_phone, get_customer_by_id, 
  get_details_by_id, get_data_usage, enable_roaming, refuel_data, 
  transfer_to_human_agents, etc.
- The CUSTOMER can run tools on their device: check_network_status, 
  run_speed_test, toggle_airplane_mode, check_status_bar, toggle_data, etc.

For technical support, the policy describes tools the customer can run 
on their device. YOU CANNOT call these customer tools directly. Instead:
- Guide the customer to run the appropriate tool on their device
- Ask them to tell you the results
- Use those results to diagnose and solve their issue
- Example: "Please check your network status and let me know what you see" 
  rather than trying to call check_network_status yourself

Be methodical, accurate, and customer-focused in your approach.
"""
```

### Key Improvements

1. **Explicit categorization**: Lists specific tools the agent CAN call vs. tools the customer runs
2. **Direct prohibition**: "YOU CANNOT call these customer tools directly"
3. **Action guidance**: Shows the correct interaction pattern with concrete example
4. **Maintains troubleshooting intent**: All diagnostic steps remain valid, just with correct interaction model
5. **Preserves methodical approach**: Encourages the same systematic problem-solving, properly directed

### Files Modified

```
experiments/configs/tau2bench_telecom.toml            (production config)
experiments/configs/tau2bench_telecom_focused.toml     (focused testing)
experiments/configs/tau2bench_telecom_fixed.toml       (validation config)
```

---

## Testing & Validation

### Before Fix
```bash
./experiments/scripts/run-telecom-eval.sh --focused --num-tasks 20
# Result: 18/20 tasks failed (90% failure rate)
# 245 invalid tool calls
# 2 successful completions (10%)
```

### After Fix (Expected)
```bash
./experiments/scripts/run-telecom-eval.sh --focused --num-tasks 20
# Expected: <5% invalid tool calls
# Model instructs customers to run device tools
# Only assistant/ tools called directly
# Success rate >60%
```

### Validation Criteria

✅ **Tool Usage**:
- Zero attempts to call user device tools directly
- Successful completion of assistant tool calls
- Proper instruction language: "Please check...", "Can you run...", "Try toggling..."

✅ **Conversation Quality**:
- Model waits for customer feedback before next step
- Diagnostic flow: instruct → receive feedback → analyze → next instruction
- Appropriate escalation only when truly needed

✅ **Task Completion**:
- Technical support scenarios resolved successfully
- Customer reaches desired outcome (e.g., "excellent" speed)
- Reduced premature transfers to human agents

---

## Lessons Learned

### For Prompt Engineering

1. **Avoid ambiguous pronouns in multi-agent contexts**: 
   - "You must understand" when describing another agent's actions creates confusion
   - Be explicit: "The customer will run these tools" vs. "You will run these tools"

2. **Distinguish tool descriptions from tool access**:
   - Describing what a tool does ≠ giving permission to call it
   - Add explicit access control statements

3. **Use clear role boundaries**:
   - When multiple roles have tools, state which role can call which
   - Consider: "You (agent) can call X. The customer can run Y."

4. **Provide concrete examples**:
   - Don't just describe the pattern, show it
   - Include both correct and incorrect examples

5. **Be careful with function-call syntax in documentation**:
   - If using `tool_name()` syntax in policies, clarify it's documentation not invocation
   - Consider alternative syntax like "the tool called 'tool_name'" instead of "tool_name()"

6. **Test prompts with literal interpretations**:
   - Models will take instructions literally
   - "You will help them perform actions" can mean "you perform" not "you instruct"

### For Eval Design

1. **Sample-level debugging is critical**:
   - Aggregate metrics (90% failure) trigger investigation
   - Individual conversation analysis reveals root cause
   - First 3-5 samples often show the pattern

2. **Error messages are diagnostic gold**:
   - "Invalid tool name" revealed the prefix mismatch
   - Error counts by tool showed the systematic nature
   - Pay attention to error patterns, not just error rates

3. **Prefix-based routing needs prompt alignment**:
   - System architecture (assistant/ vs. user/ prefixes) must be reflected in prompts
   - Silent prefix addition without prompt clarification causes confusion

4. **High failure rates warrant log analysis before model debugging**:
   - 90% failure suggests systematic issue, not model quality
   - Check configuration before assuming model problems
   - Sample conversations faster than full re-runs

### For Multi-Agent Systems

1. **Tool namespacing must be reflected in prompts**:
   - If the system separates tool sets by prefix, make this explicit
   - Don't rely on implicit understanding of system architecture

2. **Simulated multi-agent interactions need clear protocols**:
   - When one agent (customer) has tools the other (support) doesn't
   - Define the coordination protocol explicitly
   - Make the interaction pattern concrete

3. **Remote actions vs. instruction must be distinguished**:
   - The difference between "do X" and "tell them to do X" must be unambiguous
   - Consider adding role markers: "You [agent] cannot X. Instead, ask the customer [user] to X."

4. **Testing should include cross-role scenarios**:
   - Test that agents don't overstep their boundaries
   - Verify correct delegation and feedback loops
   - Check that the human-in-the-loop model works as designed

---

## Impact Assessment

### Severity: **HIGH**

- 90% of tasks failing due to this single issue
- Completely blocked technical support evaluation scenarios
- Made evaluation results meaningless for model comparison
- Prevented valid assessment of model capabilities

### Affected Components

- ✅ **Tau2bench telecom domain**: Directly affected
- ⚠️ **Tau2bench retail/airline domains**: May have similar issues - recommend checking
- ❌ **Model deployment**: Not affected (eval-only issue)
- ❌ **Other benchmarks**: Not affected (tau2bench-specific)

### Model Context Verification

The model under evaluation (`c4-prod-run-1`) had:
- ✅ Correct system prompt content (full policy included)
- ✅ Correct tool descriptions (comprehensive documentation)
- ✅ Correct conversation history (proper turn structure)
- ❌ Ambiguous tool access instructions (the bug)

After this fix, the model should:
- ✅ Only call assistant/ tools directly
- ✅ Instruct customers to run user/ tools
- ✅ Use customer feedback to diagnose issues
- ✅ Successfully complete technical support scenarios
- ✅ Maintain methodical troubleshooting approach

---

## Recommendations

### Immediate Actions

1. ✅ **DONE**: Update preambles in all tau2bench telecom configs
2. 🔄 **TODO**: Re-run evaluation with fixed configs (20 tasks minimum)
3. 🔄 **TODO**: Compare before/after metrics to quantify improvement
4. 🔄 **TODO**: Validate that tool call patterns match expectations

### Short-term Improvements

1. **Check other tau2bench domains**:
   - Retail and airline may have the same ambiguous preambles
   - Run focused evals (3-5 samples) to check for similar errors
   - Update preambles if needed

2. **Improve policy documentation**:
   - Update `utils/guidelines_tools.py` with clearer role distinctions
   - Consider restructuring the policy to separate agent vs. customer tools
   - Add explicit "Agent Tools" and "Customer Tools" sections

3. **Add configuration validation**:
   - Create pre-run checks that catch tool prefix mismatches
   - Validate that preamble mentions tool access boundaries
   - Warn if system prompt references tools without access control

### Long-term Improvements

1. **Documentation**:
   - Update tau2bench README with tool architecture explanation
   - Document the prefix-based routing system
   - Provide preamble templates for new domains

2. **Testing infrastructure**:
   - Add regression tests for tool call patterns
   - Check that user tools are never called with assistant/ prefix
   - Verify instruction language is used for customer tools

3. **Monitoring**:
   - Track "Invalid tool name" errors as a key metric
   - Alert on high error rates (>10% tool call failures)
   - Log tool call patterns for analysis

4. **Process**:
   - Require focused eval runs (3-5 samples) before full runs
   - Sample-level review for new configurations
   - Checklist for multi-agent evaluation setups

---

## References

### Original Analysis
- **Log file**: `output/bee_run_0ac12b3e_20251013_161135.jsonl`
- **Summary**: `output/bee_run_0ac12b3e_20251013_161135_summary.json`
- **Run command**: `./experiments/scripts/run-telecom-eval.sh --focused --num-tasks 20`

### Code References
- **Tool routing**: `~/dev/apiary/comb/comb/envs/tau2bench/builder.py` (lines 572-579, 599, 665)
- **System prompt**: `~/dev/apiary/comb/comb/envs/tau2bench/utils/chatbot_system_prompt.py`
- **Guidelines**: `~/dev/apiary/comb/comb/envs/tau2bench/utils/guidelines_tools.py`

### Configuration Files
- **Fixed configs**:
  - `experiments/configs/tau2bench_telecom.toml`
  - `experiments/configs/tau2bench_telecom_focused.toml`
  - `experiments/configs/tau2bench_telecom_fixed.toml`

### Related Documentation
- **Failures directory**: `experiments/failures/README.md`
- **Local setup**: `experiments/LOCAL_SETUP.md`
- **MCP solution**: `experiments/LOCAL_MCP_SOLUTION.md`

---

## Contact

For questions about this analysis or the fix:
- **Team**: eval-ds
- **Related issue**: Tool confusion in multi-agent evaluation scenarios
- **Status**: Fixed, pending validation

