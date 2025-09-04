#!/usr/bin/env python3
"""
Simple script to load bee run samples and prepare them for analysis.

This script demonstrates how to:
1. Connect to the BeeDB database
2. Load samples from a specific bee run or task run
3. Convert samples to pandas DataFrame for analysis
4. Basic data exploration and statistics
"""

import asyncio
import logging
import uuid
from typing import Optional, List
import pandas as pd
import numpy as np
from checkpoint_metadata_client.client import BeeRunClient, TaskRunClient, SampleClient


class BeeRunLoader:
    """Loads and processes bee run data for analysis."""
    
    def __init__(self, environment: str = "production", use_sa: bool = True, verbose: bool = False):
        """
        Initialize the bee run loader.
        
        Args:
            environment: "staging" or "production"
            use_sa: Whether to use service account authentication
            verbose: Enable verbose logging
        """
        self.bee_client = BeeRunClient(environment=environment, use_sa=use_sa)
        self.task_client = TaskRunClient(environment=environment, use_sa=use_sa)
        self.sample_client = SampleClient(environment=environment, use_sa=use_sa)
        
        if not verbose:
            # Set log level to only show warnings and above
            for client in (self.bee_client, self.task_client, self.sample_client):
                client.logger.setLevel(logging.WARNING)
    
    async def load_bee_run_info(self, bee_run_id: str) -> dict:
        """Load basic information about a bee run."""
        try:
            bee_run = await self.bee_client.get_by_id(uuid.UUID(bee_run_id))
            if not bee_run:
                print(f"❌ No bee run found with ID: {bee_run_id}")
                return {}
            
            return {
                "bee_run_id": str(bee_run.id),
                "created_at": bee_run.created_at,
                "bee_run_config": bee_run.bee_run_config,
                "bee_run_metadata": bee_run.bee_run_metadata,
                "wandb_run_url": bee_run.wandb_run_url,
                "wandb_user": bee_run.wandb_user,
            }
        except Exception as e:
            print(f"❌ Error loading bee run info: {e}")
            return {}
    
    async def load_task_runs_for_bee_run(self, bee_run_id: str) -> List[dict]:
        """Load all task runs associated with a bee run."""
        try:
            task_runs = await self.task_client.get_by_bee_run(uuid.UUID(bee_run_id))
            
            task_run_info = []
            for task_run in task_runs:
                info = {
                    "task_run_id": str(task_run.id),
                    "task_name": task_run.task_name,
                    "estimator_name": task_run.estimator_name,
                    "metrics": task_run.metrics,
                    "task_metadata": task_run.task_metadata,
                    "created_at": task_run.created_at,
                }
                task_run_info.append(info)
            
            return task_run_info
        except Exception as e:
            print(f"❌ Error loading task runs: {e}")
            return []
    
    async def load_samples_for_task_run(self, task_run_id: str, limit: Optional[int] = None) -> List[dict]:
        """Load samples for a specific task run."""
        try:
            samples = await self.sample_client.get_by_task(task_run_id=uuid.UUID(task_run_id))
            
            if limit:
                samples = samples[:limit]
            
            sample_data = []
            for sample in samples:
                sample_dict = {
                    "sample_id": str(sample.id),
                    "prompt_hash": str(sample.prompt_hash),
                    "outputs": sample.outputs,
                    "metrics": sample.metrics,
                    "debug_info": sample.debug_info,
                    "task_run_id": str(sample.task_run_id),
                }
                sample_data.append(sample_dict)
            
            return sample_data
        except Exception as e:
            print(f"❌ Error loading samples: {e}")
            return []
    
    def samples_to_dataframe(self, samples: List[dict]) -> pd.DataFrame:
        """Convert samples to a pandas DataFrame for analysis."""
        if not samples:
            return pd.DataFrame()
        
        # Flatten the nested structures
        flattened_samples = []
        for sample in samples:
            flat_sample = {
                "sample_id": sample["sample_id"],
                "prompt_hash": sample["prompt_hash"],
                "task_run_id": sample["task_run_id"],
            }
            
            # Add outputs (flatten if nested)
            if isinstance(sample["outputs"], dict):
                for key, value in sample["outputs"].items():
                    flat_sample[f"output_{key}"] = value
            else:
                flat_sample["output"] = sample["outputs"]
            
            # Add metrics
            if sample["metrics"]:
                for key, value in sample["metrics"].items():
                    flat_sample[f"metric_{key}"] = value
            
            # Add debug info
            if sample["debug_info"]:
                for key, value in sample["debug_info"].items():
                    flat_sample[f"debug_{key}"] = value
            
            flattened_samples.append(flat_sample)
        
        return pd.DataFrame(flattened_samples)
    
    def analyze_samples(self, df: pd.DataFrame) -> None:
        """Perform basic analysis on the samples DataFrame."""
        if df.empty:
            print("📊 No data to analyze")
            return
        
        print("\n📊 SAMPLE ANALYSIS")
        print("=" * 50)
        
        print(f"🔢 Total samples: {len(df)}")
        print(f"📋 Columns: {len(df.columns)}")
        
        # Show basic info about the dataframe
        print(f"\n📝 DataFrame Info:")
        print(f"  Shape: {df.shape}")
        print(f"  Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        # Show column types
        print(f"\n📊 Column Types:")
        type_counts = df.dtypes.value_counts()
        for dtype, count in type_counts.items():
            print(f"  {dtype}: {count} columns")
        
        # Show some sample data
        print(f"\n📋 Sample Data (first 3 rows):")
        display_columns = df.columns[:10] if len(df.columns) > 10 else df.columns
        print(df[display_columns].head(3).to_string())
        
        # Analyze metric columns
        metric_cols = [col for col in df.columns if col.startswith('metric_')]
        if metric_cols:
            print(f"\n📈 Metrics Summary ({len(metric_cols)} metrics):")
            metrics_df = df[metric_cols]
            print(metrics_df.describe())
        
        # Show missing data
        missing_data = df.isnull().sum()
        missing_data = missing_data[missing_data > 0]
        if not missing_data.empty:
            print(f"\n❓ Missing Data:")
            for col, count in missing_data.items():
                pct = (count / len(df)) * 100
                print(f"  {col}: {count} ({pct:.1f}%)")


async def main():
    """Main function to demonstrate loading bee run data."""
    print("🐝 Bee Run Data Loader")
    print("=" * 50)
    
    # Configuration - you can modify these
    BEE_RUN_ID = "your-bee-run-id-here"  # Replace with actual bee run ID from discover_runs.py
    ENVIRONMENT = "production"  # or "staging"
    SAMPLE_LIMIT = 100  # Limit samples for testing, set to None for all
    
    print(f"🔧 Configuration:")
    print(f"  Environment: {ENVIRONMENT}")
    print(f"  Sample limit: {SAMPLE_LIMIT}")
    
    # Check if placeholder ID is being used
    if BEE_RUN_ID == "your-bee-run-id-here":
        print("\n⚠️  Please replace 'your-bee-run-id-here' with an actual bee run ID!")
        print("📝 Example bee run ID format: '12345678-1234-1234-1234-123456789abc'")
                    print("💡 Use 'uv run python bee_search.py --help' to find available bee run IDs")
        print("🔍 The discovery tool will show recent runs with their IDs, tasks, and models")
        return
    
    # Initialize the loader
    loader = BeeRunLoader(environment=ENVIRONMENT, use_sa=True, verbose=False)
    
    try:
        # Example 1: Load bee run info
        print(f"\n1️⃣ Loading bee run info for ID: {BEE_RUN_ID}")
        bee_run_info = await loader.load_bee_run_info(BEE_RUN_ID)
        
        if bee_run_info:
            print(f"✅ Found bee run created at: {bee_run_info.get('created_at', 'unknown')}")
            if bee_run_info.get('wandb_run_url'):
                print(f"🔗 W&B URL: {bee_run_info['wandb_run_url']}")
        
        # Example 2: Load task runs
        print(f"\n2️⃣ Loading task runs for bee run...")
        task_runs = await loader.load_task_runs_for_bee_run(BEE_RUN_ID)
        
        if task_runs:
            print(f"✅ Found {len(task_runs)} task runs:")
            for i, task_run in enumerate(task_runs[:5]):  # Show first 5
                print(f"  {i+1}. {task_run['task_name']} - {task_run['estimator_name']}")
                if task_run['metrics']:
                    sample_metrics = list(task_run['metrics'].keys())[:3]
                    print(f"     Metrics: {sample_metrics}...")
            
            if len(task_runs) > 5:
                print(f"     ... and {len(task_runs) - 5} more")
        
        # Example 3: Load samples for the first task run
        if task_runs:
            print(f"\n3️⃣ Loading samples for first task run...")
            first_task_run = task_runs[0]
            task_run_id = first_task_run['task_run_id']
            
            print(f"📝 Loading samples from: {first_task_run['task_name']} - {first_task_run['estimator_name']}")
            samples = await loader.load_samples_for_task_run(task_run_id, limit=SAMPLE_LIMIT)
            
            if samples:
                print(f"✅ Loaded {len(samples)} samples")
                
                # Convert to DataFrame
                df = loader.samples_to_dataframe(samples)
                
                # Analyze the data
                loader.analyze_samples(df)
                
                # Save to CSV for further analysis
                output_file = f"bee_run_samples_{BEE_RUN_ID[:8]}.csv"
                df.to_csv(output_file, index=False)
                print(f"\n💾 Saved samples to: {output_file}")
                
        print(f"\n✅ Data loading complete!")
        
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
