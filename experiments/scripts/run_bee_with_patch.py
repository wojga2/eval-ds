#!/usr/bin/env python3
"""
Wrapper script that patches tau2bench before running bee.
This ensures the patch is applied regardless of Python environment setup.
"""

import sys
import os

# Add project scripts to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'scripts'))

def apply_patch():
    """Apply the tau2bench MCP server patch"""
    try:
        # Import and patch
        from bee.tasks.library.tau2_bench.tau2_bench_task import Tau2BenchTask
        from comb.envs.tau2bench.builder import Tau2BenchScenarioConfig
        from hive import BaseEstimator, ChatSample
        from comb import interface as comb_interface
        import functools
        
        # Save original method
        original_run_estimator = Tau2BenchTask.run_estimator
        
        async def patched_run_estimator(self, sample: ChatSample, estimator: BaseEstimator):
            """Patched version that overrides tool_env_per_domain to use local servers"""
            sampler_fn = functools.partial(self.sampler_fn, estimator=estimator)
            data_item = comb_interface.CommandDataCombItem(**sample.inputs.data_item)
            scenario_config: Tau2BenchScenarioConfig = self.scenario_builder.get_default_scenario_config(
                data_item=data_item
            )
            
            # Get local MCP server URLs (with /mcp endpoint)
            local_tool_env = {
                "airline": {
                    "type": "http",
                    "name": "airline",
                    "server_uri": "http://127.0.0.1:8100/mcp",
                    "version": "local",
                },
                "retail": {
                    "type": "http",
                    "name": "retail",
                    "server_uri": "http://127.0.0.1:8101/mcp",
                    "version": "local",
                },
                "telecom": {
                    "type": "http",
                    "name": "telecom",
                    "server_uri": "http://127.0.0.1:8102/mcp",
                    "version": "local",
                },
            }
            
            # Override scenario config with local MCP servers + estimator settings
            scenario_config = scenario_config.model_copy(
                update={
                    "user_estimator_class": self.user_estimator_class,
                    "user_estimator_kwargs": self.user_estimator_kwargs,
                    "nl_assertion_judge_estimator_class": self.nl_assertion_judge_class,
                    "nl_assertion_judge_estimator_kwargs": self.nl_assertion_judge_kwargs,
                    "tool_env_per_domain": local_tool_env,  # ← OVERRIDE HERE
                }
            )
            
            scenario = await self.scenario_builder(
                data_item=data_item,
                scenario_config=scenario_config,
                sampler_fn=sampler_fn,
            )
            
            # Continue with original logic
            from comb.utils.exception import CombParsingError
            rollout: comb_interface.RolloutOutput = await scenario.unroll(
                max_steps=self.max_steps,
                exceptions_to_catch=(CombParsingError,),
            )
            
            from comb.shared import tmp_data_utils
            from hive.data.chat import Turn
            fatuc_turns = tmp_data_utils.convert_agent_traj_turns_to_fatuc_turns(rollout.speaker_outputs[-1].turns)
            
            sample.outputs.conversation = [
                hive_turn for fatuc_turn in fatuc_turns for hive_turn in Turn.turns_from_fatuc(fatuc_turn)
            ]
            sample.outputs.reward = rollout.total_reward
            
            from bee.tasks.library.tau2_bench.pretty_print_trajectory import pretty_print_trajectory
            sample.outputs.pretty_trajectory = pretty_print_trajectory(scenario.fatuc_turns)
            
            if rollout.reward_outputs:
                last_reward = rollout.reward_outputs[-1]
                sample.outputs.reward_metrics = last_reward.metrics
                sample.outputs.reward_text_info = last_reward.text_info
                sample.outputs.reward_extras = last_reward.extras
        
        # Apply the patch
        Tau2BenchTask.run_estimator = patched_run_estimator
        
        print("✅ Patched Tau2BenchTask to use local MCP servers:")
        print("   - airline:  http://127.0.0.1:8100/mcp")
        print("   - retail:   http://127.0.0.1:8101/mcp")
        print("   - telecom:  http://127.0.0.1:8102/mcp")
        print("")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Warning: Failed to patch tau2bench: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Apply patch
    apply_patch()
    
    # Now run bee's main
    from bee.__main__ import main
    main()

