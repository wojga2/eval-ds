#!/usr/bin/env python3
"""
Example usage of the eval-ds bee run loader.

This script shows how to load bee run data for a specific bee run ID.
You'll need to replace the BEE_RUN_ID with an actual ID from your system.
"""

import asyncio
from eval_ds.main import BeeRunLoader


async def example_usage():
    """Example of how to use the BeeRunLoader."""
    
    # Replace this with an actual bee run ID from discover_runs.py
    # Example from recent runs:
    BEE_RUN_ID = "0af9f3c4-4513-40d9-94bb-76ab1fd08479"
    
    # Initialize the loader
    loader = BeeRunLoader(environment="production", use_sa=True, verbose=True)
    
    print("🐝 Loading bee run data...")
    
    # Load bee run information
    bee_run_info = await loader.load_bee_run_info(BEE_RUN_ID)
    if bee_run_info:
        print(f"✅ Found bee run: {bee_run_info['bee_run_id']}")
    
    # Load associated task runs
    task_runs = await loader.load_task_runs_for_bee_run(BEE_RUN_ID)
    print(f"📋 Found {len(task_runs)} task runs")
    
    # Load samples for the first task run (limited to 50 samples)
    if task_runs:
        samples = await loader.load_samples_for_task_run(task_runs[0]['task_run_id'], limit=50)
        print(f"📊 Loaded {len(samples)} samples")
        
        # Convert to DataFrame and analyze
        df = loader.samples_to_dataframe(samples)
        loader.analyze_samples(df)


if __name__ == "__main__":
    asyncio.run(example_usage())
