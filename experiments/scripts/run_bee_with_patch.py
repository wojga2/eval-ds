#!/usr/bin/env python3
"""
Python wrapper to patch Tau2BenchTask to use local MCP servers.

This patches Tau2BenchTask.run_estimator() to override tool_env_per_domain
in the scenario config, redirecting MCP connections to localhost.
"""
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def patch_tau2bench_mcp_urls():
    """Patch Tau2BenchTask.run_estimator() to use local MCP servers."""
    try:
        from comb.envs.tau2bench.builder import Tau2BenchTask
        
        # Store original run_estimator
        original_run_estimator = Tau2BenchTask.run_estimator
        
        # Define local MCP server configuration
        LOCAL_TOOL_ENV = {
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
        
        # Define patched run_estimator
        async def patched_run_estimator(self, estimator, sample_id):
            """Patched version that overrides MCP server URLs before execution."""
            # Get the scenario config
            scenario_config = self.get_scenario(sample_id)
            
            # Override tool_env_per_domain with local servers
            scenario_config = scenario_config.model_copy(
                update={
                    "tool_env_per_domain": LOCAL_TOOL_ENV,
                }
            )
            
            # Store patched config back
            self.scenario_per_sample_id[sample_id] = scenario_config
            
            # Call original run_estimator
            return await original_run_estimator(self, estimator, sample_id)
        
        # Apply patch
        Tau2BenchTask.run_estimator = patched_run_estimator
        
        logger.info("✅ Patched Tau2BenchTask to use local MCP servers:")
        logger.info("   - airline:  http://127.0.0.1:8100/mcp")
        logger.info("   - retail:   http://127.0.0.1:8101/mcp")
        logger.info("   - telecom:  http://127.0.0.1:8102/mcp")
        
    except ImportError as e:
        logger.error(f"⚠️  Could not patch Tau2BenchTask: {e}")
        logger.error("   This is expected if tau2bench is not being used")
    except Exception as e:
        logger.error(f"⚠️  Error patching Tau2BenchTask: {e}")

def main():
    """Apply patches and run bee."""
    # Apply MCP server patches
    patch_tau2bench_mcp_urls()
    
    # Import and run bee
    from bee.__main__ import main as bee_main
    bee_main()

if __name__ == "__main__":
    main()
