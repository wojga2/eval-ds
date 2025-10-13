#!/usr/bin/env python3
"""
Wrapper script that patches tau2bench before running bee.
This ensures the patch is applied regardless of Python environment setup.
"""

import sys
import os
import logging

# Add project root to path
eval_ds_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, eval_ds_root)

# Import prompt patch loader
from prompt_patch_loader import load_patches

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
            """Patched version that overrides tool_env_per_domain to use local servers and applies prompt patches"""
            # Load prompt patches from config if specified
            prompt_patch_ids = getattr(self, '_prompt_patch_ids', [])
            if prompt_patch_ids:
                try:
                    import sys
                    sys.stderr.write(f"🔧 [WORKER] Loading patches: {prompt_patch_ids}\n")
                    sys.stderr.flush()
                    
                    prompt_patches = load_patches(prompt_patch_ids)
                    sys.stderr.write(f"✅ [WORKER] Loaded {len(prompt_patches)} patches, total chars: {sum(len(p) for p in prompt_patches)}\n")
                    sys.stderr.flush()
                    
                    # Inject patches into BOTH the utils module AND the builder's imported reference
                    from comb.envs.tau2bench.utils import chatbot_system_prompt as prompt_module
                    from comb.envs.tau2bench import builder as builder_module
                    
                    original_get_prompt = prompt_module.get_chatbot_system_prompt
                    
                    def patched_get_prompt(policy: str, **kwargs):
                        sys.stderr.write(f"📝 [WORKER] get_chatbot_system_prompt called, applying {len(prompt_patches)} patches\n")
                        sys.stderr.flush()
                        return original_get_prompt(policy, prompt_patches=prompt_patches)
                    
                    # Patch both places where the function might be referenced
                    prompt_module.get_chatbot_system_prompt = patched_get_prompt
                    builder_module.get_chatbot_system_prompt = patched_get_prompt
                    sys.stderr.write(f"✅ [WORKER] Patched get_chatbot_system_prompt in utils and builder\n")
                    sys.stderr.flush()
                except Exception as e:
                    import traceback
                    sys.stderr.write(f"❌ [WORKER] Failed to load prompt patches {prompt_patch_ids}: {e}\n")
                    sys.stderr.write(traceback.format_exc())
                    sys.stderr.flush()
            
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
        
        # Patch __init__ to extract prompt_patches from config
        original_init = Tau2BenchTask.__init__
        
        def patched_init(self, config):
            # Extract prompt_patches if present
            try:
                # Try to get prompt_patches as a list
                patch_ids = []
                if hasattr(config, 'get'):
                    # Try get method
                    try:
                        patches_str = config.get('prompt_patches', None)
                        if patches_str:
                            patch_ids = patches_str if isinstance(patches_str, list) else [patches_str]
                    except:
                        pass
                
                # Store for use in run_estimator
                self._prompt_patch_ids = patch_ids
                
                if patch_ids:
                    print(f"📝 Loaded prompt patches: {', '.join(patch_ids)}")
            except Exception as e:
                print(f"⚠️  Warning: Failed to extract prompt_patches from config: {e}")
                self._prompt_patch_ids = []
            
            # Call original init
            original_init(self, config)
        
        Tau2BenchTask.__init__ = patched_init
        
        # Patch check_unused_options to allow prompt_patches field
        from bee.workers import check_unused_options
        original_check = check_unused_options
        
        def patched_check_unused_options(tasks, estimators, run_config):
            """Patched version that allows prompt_patches in task config"""
            # Call original check but catch the error to filter prompt_patches
            try:
                return original_check(tasks, estimators, run_config)
            except ValueError as e:
                error_msg = str(e)
                # If error mentions prompt_patches, try to handle it
                if 'prompt_patches' in error_msg:
                    # Parse and filter the error
                    # Just log a warning and continue
                    print("⚠️  Note: prompt_patches is a custom field (this is expected)")
                    return  # Success
                else:
                    # Re-raise if it's a different validation error
                    raise
        
        # Replace in module
        import bee.workers
        bee.workers.check_unused_options = patched_check_unused_options
        
        # Apply the run_estimator patch
        Tau2BenchTask.run_estimator = patched_run_estimator
        
        print("✅ Patched Tau2BenchTask to use local MCP servers:")
        print("   - airline:  http://127.0.0.1:8100/mcp")
        print("   - retail:   http://127.0.0.1:8101/mcp")
        print("   - telecom:  http://127.0.0.1:8102/mcp")
        print("✅ Patched Tau2BenchTask to support prompt patches")
        print("")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Warning: Failed to patch tau2bench: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Apply MCP server patch
    apply_patch()
    
    # Reduce verbose logging from MCP client and streaming (do this after imports)
    logging.getLogger('mcp.client.streamable_http').setLevel(logging.CRITICAL)
    logging.getLogger('mcp.client').setLevel(logging.CRITICAL)
    logging.getLogger('cohere_mcp_client').setLevel(logging.CRITICAL)
    logging.getLogger('cohere_mcp_client.clients').setLevel(logging.CRITICAL)
    logging.getLogger('cohere_mcp_client.streaming_client').setLevel(logging.CRITICAL)
    
    # Suppress all streaming progress messages
    logging.getLogger('').setLevel(logging.WARNING)  # Root logger
    
    # But keep bee's important loggers at INFO
    logging.getLogger('bee').setLevel(logging.INFO)
    logging.getLogger('api').setLevel(logging.WARNING)
    
    # Now run bee's main
    from bee.__main__ import main
    main()

