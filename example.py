#!/usr/bin/env python3
"""
Comprehensive example usage of the eval-ds bee run loader.

This script demonstrates how to:
1. Load comprehensive bee run metadata
2. Fetch ALL samples from a bee run (not just limited samples)
3. Extract detailed metadata from bee runs, task runs, and samples
4. Implement a mock iteration loop over samples with metadata analysis
5. Provide comprehensive data exploration capabilities
6. Export results to JSON and CSV formats

You'll need to replace the BEE_RUN_ID with an actual ID from your system.
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
from eval_ds.main import BeeRunLoader


class BeeRunAnalyzer:
    """Comprehensive analyzer for bee run data exploration."""
    
    def __init__(self, environment: str = "production", use_sa: bool = True, verbose: bool = True):
        """Initialize the analyzer."""
        self.loader = BeeRunLoader(environment=environment, use_sa=use_sa, verbose=verbose)
        self.bee_run_metadata = {}
        self.task_runs_metadata = []
        self.all_samples = []
    
    async def extract_comprehensive_bee_run_metadata(self, bee_run_id: str) -> Dict[str, Any]:
        """Extract comprehensive metadata from a bee run."""
        print("\n🔍 EXTRACTING COMPREHENSIVE BEE RUN METADATA")
        print("=" * 60)
        
        bee_run_info = await self.loader.load_bee_run_info(bee_run_id)
        if not bee_run_info:
            print(f"❌ Failed to load bee run info for ID: {bee_run_id}")
            return {}
        
        # Extract detailed metadata
        metadata = {
            "bee_run_id": bee_run_info.get("bee_run_id"),
            "created_at": bee_run_info.get("created_at"),
            "wandb_user": bee_run_info.get("wandb_user"),
            "wandb_run_url": bee_run_info.get("wandb_run_url"),
            "bee_run_config": bee_run_info.get("bee_run_config", {}),
            "bee_run_metadata": bee_run_info.get("bee_run_metadata", {}),
        }
        
        # Extract config details if available (try multiple possible config attributes)
        config = metadata.get("bee_run_config") or metadata.get("config") or {}
        if config:
            metadata.update({
                "config_tasks": list(config.get("tasks", {}).keys()) if isinstance(config, dict) and "tasks" in config else [],
                "config_estimators": list(config.get("estimators", {}).keys()) if isinstance(config, dict) and "estimators" in config else [],
                "config_raw": config
            })
        else:
            metadata.update({
                "config_tasks": [],
                "config_estimators": [],
                "config_raw": {}
            })
        
        # Print metadata summary
        print(f"✅ Bee Run ID: {metadata['bee_run_id']}")
        print(f"👤 User: {metadata['wandb_user']}")
        print(f"📅 Created: {metadata['created_at']}")
        if metadata.get('wandb_run_url'):
            print(f"🔗 W&B URL: {metadata['wandb_run_url']}")
        
        if metadata['config_tasks']:
            print(f"📋 Configured Tasks ({len(metadata['config_tasks'])}): {', '.join(metadata['config_tasks'][:5])}")
            if len(metadata['config_tasks']) > 5:
                print(f"    ... and {len(metadata['config_tasks']) - 5} more")
        
        if metadata['config_estimators']:
            print(f"🤖 Configured Estimators ({len(metadata['config_estimators'])}): {', '.join(metadata['config_estimators'][:3])}")
            if len(metadata['config_estimators']) > 3:
                print(f"    ... and {len(metadata['config_estimators']) - 3} more")
        
        self.bee_run_metadata = metadata
        return metadata
    
    async def extract_comprehensive_task_runs_metadata(self, bee_run_id: str) -> List[Dict[str, Any]]:
        """Extract comprehensive metadata from all task runs."""
        print("\n📋 EXTRACTING COMPREHENSIVE TASK RUNS METADATA")
        print("=" * 60)
        
        task_runs = await self.loader.load_task_runs_for_bee_run(bee_run_id)
        if not task_runs:
            print("❌ No task runs found")
            return []
        
        task_runs_metadata = []
        for i, task_run in enumerate(task_runs):
            print(f"\n📊 Task Run {i+1}/{len(task_runs)}: {task_run['task_name']}")
            
            # Extract comprehensive metadata
            metadata = {
                "task_run_id": task_run["task_run_id"],
                "task_name": task_run["task_name"],
                "estimator_name": task_run["estimator_name"],
                "created_at": task_run["created_at"],
                "metrics": task_run.get("metrics", {}),
                "task_metadata": task_run.get("task_metadata", {}),
                
                # Analysis of metrics
                "metrics_count": len(task_run.get("metrics", {})),
                "metrics_keys": list(task_run.get("metrics", {}).keys()),
                "has_success_metrics": any("success" in k.lower() for k in task_run.get("metrics", {}).keys()),
                "has_accuracy_metrics": any("accuracy" in k.lower() for k in task_run.get("metrics", {}).keys()),
                
                # Analysis of task metadata
                "task_metadata_keys": list(task_run.get("task_metadata", {}).keys()),
                "task_status": task_run.get("task_metadata", {}).get("eval_run_status", "unknown"),
            }
            
            # Print task run summary
            print(f"  🤖 Estimator: {metadata['estimator_name']}")
            print(f"  📊 Status: {metadata['task_status']}")
            print(f"  📈 Metrics ({metadata['metrics_count']}): {', '.join(metadata['metrics_keys'][:5])}")
            if len(metadata['metrics_keys']) > 5:
                print(f"      ... and {len(metadata['metrics_keys']) - 5} more")
            
            if metadata['task_metadata_keys']:
                print(f"  🔧 Metadata Keys: {', '.join(metadata['task_metadata_keys'][:3])}")
                if len(metadata['task_metadata_keys']) > 3:
                    print(f"      ... and {len(metadata['task_metadata_keys']) - 3} more")
            
            task_runs_metadata.append(metadata)
        
        print(f"\n✅ Processed {len(task_runs_metadata)} task runs")
        self.task_runs_metadata = task_runs_metadata
        return task_runs_metadata
    
    async def fetch_all_samples_from_bee_run(self, bee_run_id: str) -> List[Dict[str, Any]]:
        """Fetch ALL samples from all task runs in a bee run."""
        print("\n📊 FETCHING ALL SAMPLES FROM BEE RUN")
        print("=" * 60)
        
        if not self.task_runs_metadata:
            await self.extract_comprehensive_task_runs_metadata(bee_run_id)
        
        all_samples = []
        total_samples_count = 0
        
        for i, task_run in enumerate(self.task_runs_metadata):
            task_run_id = task_run["task_run_id"]
            task_name = task_run["task_name"]
            estimator_name = task_run["estimator_name"]
            
            print(f"\n📥 Loading samples for Task Run {i+1}: {task_name}")
            print(f"   🤖 Estimator: {estimator_name}")
            
            # Fetch ALL samples (no limit)
            samples = await self.loader.load_samples_for_task_run(task_run_id, limit=None)
            
            if samples:
                print(f"   ✅ Loaded {len(samples)} samples")
                
                # Add task run metadata to each sample
                for sample in samples:
                    sample_with_metadata = {
                        **sample,  # Original sample data
                        "task_name": task_name,
                        "estimator_name": estimator_name,
                        "task_run_metadata": task_run,
                    }
                    all_samples.append(sample_with_metadata)
                
                total_samples_count += len(samples)
            else:
                print(f"   ⚠️ No samples found")
        
        print(f"\n🎯 TOTAL SAMPLES LOADED: {total_samples_count}")
        print(f"📊 From {len(self.task_runs_metadata)} task runs")
        
        self.all_samples = all_samples
        return all_samples
    
    def extract_sample_metadata_statistics(self, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract comprehensive statistics from sample metadata."""
        if not samples:
            return {}
        
        print("\n🔬 ANALYZING SAMPLE METADATA")
        print("=" * 60)
        
        # Basic statistics
        stats = {
            "total_samples": len(samples),
            "unique_task_runs": len(set(s.get("task_run_id") for s in samples)),
            "unique_tasks": len(set(s.get("task_name") for s in samples)),
            "unique_estimators": len(set(s.get("estimator_name") for s in samples)),
            "unique_prompt_hashes": len(set(s.get("prompt_hash") for s in samples)),
        }
        
        # Analyze outputs structure
        output_types = set()
        output_keys = set()
        for sample in samples:
            outputs = sample.get("outputs", {})
            if isinstance(outputs, dict):
                output_keys.update(outputs.keys())
                output_types.add("dict")
            else:
                output_types.add(type(outputs).__name__)
        
        stats.update({
            "output_types": list(output_types),
            "output_keys": list(output_keys),
        })
        
        # Analyze metrics structure
        all_metric_keys = set()
        samples_with_metrics = 0
        for sample in samples:
            metrics = sample.get("metrics", {})
            if metrics:
                samples_with_metrics += 1
                if isinstance(metrics, dict):
                    all_metric_keys.update(metrics.keys())
        
        stats.update({
            "samples_with_metrics": samples_with_metrics,
            "metric_keys": list(all_metric_keys),
            "metrics_coverage": samples_with_metrics / len(samples) if samples else 0,
        })
        
        # Analyze debug info structure
        debug_info_keys = set()
        samples_with_debug = 0
        for sample in samples:
            debug_info = sample.get("debug_info", {})
            if debug_info:
                samples_with_debug += 1
                if isinstance(debug_info, dict):
                    debug_info_keys.update(debug_info.keys())
        
        stats.update({
            "samples_with_debug_info": samples_with_debug,
            "debug_info_keys": list(debug_info_keys),
            "debug_info_coverage": samples_with_debug / len(samples) if samples else 0,
        })
        
        # Print statistics
        print(f"📊 Total Samples: {stats['total_samples']}")
        print(f"🔄 Unique Task Runs: {stats['unique_task_runs']}")
        print(f"📋 Unique Tasks: {stats['unique_tasks']}")
        print(f"🤖 Unique Estimators: {stats['unique_estimators']}")
        print(f"🔑 Unique Prompt Hashes: {stats['unique_prompt_hashes']}")
        print(f"📤 Output Types: {', '.join(stats['output_types'])}")
        if stats['output_keys']:
            print(f"🔧 Output Keys ({len(stats['output_keys'])}): {', '.join(list(stats['output_keys'])[:5])}")
            if len(stats['output_keys']) > 5:
                print(f"    ... and {len(stats['output_keys']) - 5} more")
        
        print(f"📈 Samples with Metrics: {stats['samples_with_metrics']} ({stats['metrics_coverage']:.1%})")
        if stats['metric_keys']:
            print(f"📊 Metric Keys ({len(stats['metric_keys'])}): {', '.join(list(stats['metric_keys'])[:5])}")
            if len(stats['metric_keys']) > 5:
                print(f"    ... and {len(stats['metric_keys']) - 5} more")
        
        print(f"🔬 Samples with Debug Info: {stats['samples_with_debug_info']} ({stats['debug_info_coverage']:.1%})")
        if stats['debug_info_keys']:
            print(f"🐛 Debug Info Keys ({len(stats['debug_info_keys'])}): {', '.join(list(stats['debug_info_keys'])[:5])}")
            if len(stats['debug_info_keys']) > 5:
                print(f"    ... and {len(stats['debug_info_keys']) - 5} more")
        
        return stats
    
    async def mock_iteration_loop_with_analysis(self, samples: List[Dict[str, Any]], max_iterations: int = 10):
        """Mock iteration loop that processes samples with comprehensive metadata analysis."""
        print(f"\n🔄 MOCK ITERATION LOOP - PROCESSING SAMPLES")
        print("=" * 60)
        print(f"🎯 Processing {len(samples)} total samples (showing first {max_iterations} iterations)")
        
        if not samples:
            print("❌ No samples to process")
            return
        
        # Group samples by task for organized iteration
        samples_by_task = {}
        for sample in samples:
            task_name = sample.get("task_name", "unknown")
            if task_name not in samples_by_task:
                samples_by_task[task_name] = []
            samples_by_task[task_name].append(sample)
        
        print(f"📊 Found samples from {len(samples_by_task)} different tasks")
        
        iteration_count = 0
        for task_name, task_samples in samples_by_task.items():
            print(f"\n📋 Processing Task: {task_name} ({len(task_samples)} samples)")
            
            for i, sample in enumerate(task_samples):
                if iteration_count >= max_iterations:
                    print(f"\n⏹️  Stopping mock iteration at {max_iterations} samples")
                    print(f"🔢 {len(samples) - max_iterations} samples remaining")
                    return
                
                iteration_count += 1
                await self._process_single_sample(sample, iteration_count)
                
                # Add small delay to simulate processing
                await asyncio.sleep(0.1)
        
        print(f"\n✅ Mock iteration complete! Processed {iteration_count} samples")
    
    async def _process_single_sample(self, sample: Dict[str, Any], iteration: int):
        """Process a single sample with detailed metadata extraction."""
        sample_id = sample.get("sample_id", "unknown")
        task_name = sample.get("task_name", "unknown")
        estimator_name = sample.get("estimator_name", "unknown")
        
        print(f"\n  🔄 Iteration {iteration}: Sample {sample_id[:8]}...")
        print(f"     📋 Task: {task_name}")
        print(f"     🤖 Estimator: {estimator_name}")
        
        # Analyze sample structure
        outputs = sample.get("outputs", {})
        metrics = sample.get("metrics", {})
        debug_info = sample.get("debug_info", {})
        
        # Extract key information from outputs
        if isinstance(outputs, dict) and outputs:
            output_summary = []
            for key, value in list(outputs.items())[:3]:  # Show first 3 keys
                if isinstance(value, str):
                    preview = value[:50] + "..." if len(value) > 50 else value
                    output_summary.append(f"{key}: '{preview}'")
                else:
                    output_summary.append(f"{key}: {type(value).__name__}")
            print(f"     📤 Outputs: {', '.join(output_summary)}")
        
        # Extract key metrics
        if metrics:
            metric_summary = []
            for key, value in list(metrics.items())[:3]:  # Show first 3 metrics
                if isinstance(value, (int, float)):
                    metric_summary.append(f"{key}={value:.3f}" if isinstance(value, float) else f"{key}={value}")
                else:
                    metric_summary.append(f"{key}={type(value).__name__}")
            print(f"     📊 Metrics: {', '.join(metric_summary)}")
        
        # Extract debug info
        if debug_info:
            debug_keys = list(debug_info.keys())[:3]
            print(f"     🐛 Debug Info: {', '.join(debug_keys)}")
        
        # Simulate some processing work
        processing_result = {
            "processed_at": datetime.now(),
            "sample_id": sample_id,
            "has_outputs": bool(outputs),
            "has_metrics": bool(metrics),
            "has_debug_info": bool(debug_info),
            "output_types": [type(v).__name__ for v in outputs.values()] if isinstance(outputs, dict) else [],
        }
        
        return processing_result


async def main():
    """Main function demonstrating comprehensive bee run analysis."""
    
    # Replace this with an actual bee run ID from bee_search.py  
    # Example from recent runs with actual data:
    BEE_RUN_ID = "37478369-f4fd-58f6-bde1-86f7d75e8f96"
    
    print("🚀 COMPREHENSIVE BEE RUN ANALYSIS")
    print("=" * 60)
    print(f"🎯 Target Bee Run ID: {BEE_RUN_ID}")
    print(f"⏰ Started at: {datetime.now()}")
    
    # Initialize the analyzer
    analyzer = BeeRunAnalyzer(environment="production", use_sa=True, verbose=True)
    
    try:
        # Step 1: Extract comprehensive bee run metadata
        bee_run_metadata = await analyzer.extract_comprehensive_bee_run_metadata(BEE_RUN_ID)
        if not bee_run_metadata:
            print("❌ Failed to load bee run metadata. Exiting.")
            return
        
        # Step 2: Extract comprehensive task runs metadata
        task_runs_metadata = await analyzer.extract_comprehensive_task_runs_metadata(BEE_RUN_ID)
        if not task_runs_metadata:
            print("❌ No task runs found. Exiting.")
            return
        
        # Step 3: Fetch ALL samples from the bee run
        all_samples = await analyzer.fetch_all_samples_from_bee_run(BEE_RUN_ID)
        if not all_samples:
            print("❌ No samples found. Exiting.")
            return
        
        # Step 4: Extract comprehensive sample statistics
        sample_stats = analyzer.extract_sample_metadata_statistics(all_samples)
        
        # Step 5: Convert to DataFrame for advanced analysis
        print("\n📊 CONVERTING TO DATAFRAME FOR ANALYSIS")
        print("=" * 60)
        df = analyzer.loader.samples_to_dataframe(all_samples)
        analyzer.loader.analyze_samples(df)
        
        # Step 6: Mock iteration loop with comprehensive processing
        await analyzer.mock_iteration_loop_with_analysis(all_samples, max_iterations=10)
        
        # Step 7: Final summary and file exports
        print("\n🎯 FINAL ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"🐝 Bee Run ID: {BEE_RUN_ID}")
        print(f"👤 User: {bee_run_metadata.get('wandb_user', 'unknown')}")
        print(f"📊 Total Task Runs: {len(task_runs_metadata)}")
        print(f"📈 Total Samples: {len(all_samples)}")
        print(f"🔧 DataFrame Shape: {df.shape}")
        print(f"💾 Memory Usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        
        # Save comprehensive results to JSON
        output_file = f"output/bee_run_analysis_{BEE_RUN_ID[:8]}.json"
        comprehensive_results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "bee_run_metadata": bee_run_metadata,
            "task_runs_metadata": task_runs_metadata,
            "sample_statistics": sample_stats,
            "total_samples": len(all_samples),
        }
        
        with open(output_file, 'w') as f:
            json.dump(comprehensive_results, f, indent=2, default=str)
        
        print(f"💾 Comprehensive analysis saved to: {output_file}")
        
        # Save samples DataFrame to CSV
        csv_file = f"output/bee_run_samples_{BEE_RUN_ID[:8]}.csv"
        df.to_csv(csv_file, index=False)
        print(f"📊 Samples DataFrame saved to: {csv_file}")
        
        print(f"\n✅ Analysis complete! Processed {len(all_samples)} samples from {len(task_runs_metadata)} task runs.")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())