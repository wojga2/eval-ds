#!/usr/bin/env python3
"""
Download all samples from a bee run with full metadata and trajectories.

This script:
1. Takes a bee run ID
2. Downloads all task runs and their samples
3. Extracts full agentic trajectories, judge scores, and metadata
4. Saves to JSONL file for analysis

The script fetches ALL available fields from the samples API. However, note that
some tasks may not save all output fields to the database. For example, some tasks
may save inputs.raw_prompt but not outputs.generations. The script will report
field coverage to help identify missing data.

Expected fields in outputs:
- raw_prompt: The formatted prompt sent to the model (input)
- generations: The model's text response (may be NULL if task didn't save it)
- raw_generations: Raw model response before processing (may be NULL)
- thinking: Model's reasoning/chain-of-thought (may be NULL)
- finish_reasons: Why the model stopped generating (may be NULL)

Usage:
    python download_bee_run.py --run-id "abc-123-def"
    python download_bee_run.py --run-id "abc-123-def" --output-dir ./my_data
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from checkpoint_metadata_client.client import BeeRunClient, TaskRunClient, SampleClient


class BeeRunDownloader:
    """Download all samples from a bee run with full metadata."""
    
    def __init__(self, environment: str = "production", use_sa: bool = True, verbose: bool = False):
        """Initialize the clients."""
        self.bee_client = BeeRunClient(environment=environment, use_sa=use_sa)
        self.task_client = TaskRunClient(environment=environment, use_sa=use_sa)
        self.sample_client = SampleClient(environment=environment, use_sa=use_sa)
        self.environment = environment
        self.verbose = verbose
        
        if not verbose:
            import logging
            for client in (self.bee_client, self.task_client, self.sample_client):
                client.logger.setLevel(logging.WARNING)
    
    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    async def get_bee_run_info(self, bee_run_id: UUID) -> Dict[str, Any]:
        """Get basic information about the bee run."""
        bee_run = await self.bee_client.get_by_id(bee_run_id)
        if not bee_run:
            raise ValueError(f"Bee run not found: {bee_run_id}")
        
        return {
            "bee_run_id": str(bee_run.id),
            "created_at": str(bee_run.created_at) if bee_run.created_at else None,
            "updated_at": str(bee_run.updated_at) if bee_run.updated_at else None,
            "wandb_run_id": bee_run.wandb_run_id,
            "wandb_run_url": bee_run.wandb_run_url,
            "wandb_user": bee_run.wandb_user,
            "config": bee_run.config,
            "bee_run_metadata": bee_run.bee_run_metadata,
        }
    
    async def get_task_runs(self, bee_run_id: UUID) -> List[Dict[str, Any]]:
        """Get all task runs for the bee run."""
        task_runs = await self.task_client.get_by_bee_run_id(bee_run_id)
        
        task_run_info = []
        for task_run in task_runs:
            task_run_info.append({
                "task_run_id": str(task_run.id),
                "task_name": task_run.task_name,
                "task_hash": str(task_run.task_hash),
                "estimator_name": task_run.estimator_name,
                "estimator_hash": str(task_run.estimator_hash),
                "task_metadata": task_run.task_metadata,
                "metrics": task_run.metrics,
                "eval_run_id": str(task_run.eval_run_id),
                "bee_run_id": str(task_run.bee_run_id),
                "created_at": str(task_run.created_at) if task_run.created_at else None,
                "updated_at": str(task_run.updated_at) if task_run.updated_at else None,
            })
        
        return task_run_info
    
    def _serialize_value(self, value: Any) -> Any:
        """Convert values to JSON-serializable format."""
        if isinstance(value, UUID):
            return str(value)
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif hasattr(value, '__dict__'):
            # Handle objects with __dict__
            return self._serialize_value(value.__dict__)
        else:
            return value
    
    async def get_samples_for_task(self, task_run_id: UUID, task_name: str, sample_limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all samples for a task run with full metadata.
        
        Uses a two-request strategy to work around API limitations:
        1. First request: Get all "safe" fields (outputs, metrics, debug_info, etc.)
        2. Second request: Try to get inputs data separately if supported
        3. Merge results by sample ID
        """
        self._log(f"  Downloading samples for task: {task_name}")
        
        # STRATEGY: Use two separate requests and merge by ID
        # Request 1: Get all fields EXCEPT inputs/inputs_metadata (these cause issues)
        # Request 2: Try to get inputs/inputs_metadata separately
        
        samples_by_id = {}
        
        # ===== REQUEST 1: Get all "safe" fields (maximized) =====
        try:
            # Based on testing, these fields work together:
            # NOTE: inputs and inputs_metadata are excluded as they cause validation errors
            safe_fields = ["id", "outputs", "metrics", "debug_info", "created_at", "prompt_hash"]
            
            self._log(f"    [1/2] Downloading safe fields: {', '.join(safe_fields)}")
            samples_safe = await self.sample_client.get_by_task_partial(task_run_id, fields=safe_fields)
            self._log(f"    ✅ Downloaded {len(samples_safe)} samples with safe fields")
            
            # Apply sample limit early
            if sample_limit and len(samples_safe) > sample_limit:
                samples_safe = samples_safe[:sample_limit]
                self._log(f"    Limited to {sample_limit} samples")
            
            # Store in dictionary by ID
            for sample in samples_safe:
                sample_id = sample.get("id") if isinstance(sample, dict) else str(sample.id)
                samples_by_id[sample_id] = sample
            
        except Exception as e:
            self._log(f"    ❌ Safe fields download failed: {e}")
            raise RuntimeError(f"Failed to download samples with safe fields: {e}")
        
        # ===== REQUEST 2: Try to get inputs/inputs_metadata separately =====
        # These fields are not supported in partial API, so we try full download for just these IDs
        self._log(f"    [2/2] Attempting to download inputs/inputs_metadata...")
        
        try:
            # Try getting full samples via batch API (includes inputs)
            # We'll only extract inputs/inputs_metadata from these
            batch_size = 100
            inputs_data = {}
            
            # We can't use partial API for inputs, so try get_by_task which returns full objects
            # But this may fail with 500 errors on some tasks
            try:
                full_samples = await self.sample_client.get_by_task(task_run_id)
                self._log(f"    ✅ Downloaded {len(full_samples)} full samples (includes inputs)")
                
                for sample in full_samples:
                    sample_id = str(sample.id)
                    if sample_id in samples_by_id:
                        # Extract only inputs-related fields
                        inputs_data[sample_id] = {
                            "inputs": self._serialize_value(sample.inputs) if hasattr(sample, 'inputs') and sample.inputs else None,
                            "inputs_metadata": self._serialize_value(sample.inputs_metadata) if hasattr(sample, 'inputs_metadata') and sample.inputs_metadata else None,
                        }
                
                self._log(f"    ✅ Extracted inputs data for {len(inputs_data)} samples")
                
            except Exception as full_error:
                # Expected to fail on some tasks (like BFCL)
                self._log(f"    ⚠️  Full download failed (inputs unavailable): {type(full_error).__name__}")
                self._log(f"    ℹ️  Continuing without inputs/inputs_metadata fields")
        
        except Exception as e:
            self._log(f"    ⚠️  Inputs download failed: {e}")
            self._log(f"    ℹ️  Continuing without inputs/inputs_metadata fields")
        
        # ===== MERGE: Combine both requests by ID =====
        self._log(f"    Merging data from both requests...")
        
        sample_data = []
        for sample_id, sample in samples_by_id.items():
            # Start with safe fields
            if isinstance(sample, dict):
                sample_dict = {
                    "sample_id": str(sample.get("id", sample_id)),
                    "task_run_id": str(task_run_id),
                    "task_name": task_name,
                    "created_at": str(sample.get("created_at")) if sample.get("created_at") else None,
                    "prompt_hash": str(sample.get("prompt_hash")) if sample.get("prompt_hash") else None,
                    "outputs": self._serialize_value(sample.get("outputs")),
                    "metrics": sample.get("metrics", {}),
                    "debug_info": self._serialize_value(sample.get("debug_info")),
                }
            else:
                # SampleModel object
                sample_dict = {
                    "sample_id": str(sample.id),
                    "task_run_id": str(sample.task_run_id),
                    "bee_run_id": str(sample.bee_run_id) if hasattr(sample, 'bee_run_id') else None,
                    "eval_run_id": str(sample.eval_run_id) if hasattr(sample, 'eval_run_id') else None,
                    "task_name": task_name,
                    "created_at": str(sample.created_at) if hasattr(sample, 'created_at') and sample.created_at else None,
                    "prompt_hash": str(sample.prompt_hash) if hasattr(sample, 'prompt_hash') and sample.prompt_hash else None,
                    "outputs": self._serialize_value(sample.outputs) if hasattr(sample, 'outputs') else None,
                    "metrics": sample.metrics if hasattr(sample, 'metrics') and sample.metrics else {},
                    "debug_info": self._serialize_value(sample.debug_info) if hasattr(sample, 'debug_info') else None,
                }
            
            # Add inputs data if available from second request
            if sample_id in inputs_data:
                sample_dict["inputs"] = inputs_data[sample_id]["inputs"]
                sample_dict["inputs_metadata"] = inputs_data[sample_id]["inputs_metadata"]
            else:
                sample_dict["inputs"] = None
                sample_dict["inputs_metadata"] = None
            
            sample_data.append(sample_dict)
        
        self._log(f"    ✅ Total: {len(sample_data)} samples with maximum fields")
        
        # Report field coverage
        has_inputs = sum(1 for s in sample_data if s.get("inputs") is not None)
        has_inputs_metadata = sum(1 for s in sample_data if s.get("inputs_metadata") is not None)
        self._log(f"    📊 Field coverage: inputs={has_inputs}/{len(sample_data)}, inputs_metadata={has_inputs_metadata}/{len(sample_data)}")
        
        # Report outputs field coverage (helpful to detect missing model generations)
        if sample_data and sample_data[0].get("outputs"):
            outputs_keys = sample_data[0]["outputs"].keys()
            has_generations = sum(1 for s in sample_data if s.get("outputs", {}).get("generations") is not None)
            has_raw_generations = sum(1 for s in sample_data if s.get("outputs", {}).get("raw_generations") is not None)
            has_thinking = sum(1 for s in sample_data if s.get("outputs", {}).get("thinking") is not None)
            has_raw_prompt = sum(1 for s in sample_data if s.get("outputs", {}).get("raw_prompt") is not None)
            
            self._log(f"    📊 Output fields: generations={has_generations}/{len(sample_data)}, "
                     f"raw_generations={has_raw_generations}/{len(sample_data)}, "
                     f"thinking={has_thinking}/{len(sample_data)}, "
                     f"raw_prompt={has_raw_prompt}/{len(sample_data)}")
            
            # Warn if model generations are missing
            if has_generations == 0 and has_raw_prompt > 0:
                self._log(f"    ⚠️  WARNING: Model generations are NULL but prompts exist. "
                         f"This may indicate a bug in the task code that didn't save model outputs.")
        
        return sample_data
    
    async def download_bee_run(
        self, 
        bee_run_id: str,
        output_dir: Path,
        task_filter: Optional[str] = None,
        metric_filter: Optional[str] = None,
        max_tasks: Optional[int] = None,
        sample_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Download all samples from a bee run.
        
        Args:
            bee_run_id: The bee run ID to download
            output_dir: Directory to save the output
            task_filter: Optional task name filter (substring match)
            metric_filter: Optional metric name filter (only tasks with this metric)
        
        Returns:
            Summary dict with download statistics
        """
        bee_run_uuid = UUID(bee_run_id)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🐝 Downloading bee run: {bee_run_id}")
        print(f"📁 Output directory: {output_dir}")
        
        # Get bee run info
        print("\n1️⃣ Fetching bee run information...")
        bee_run_info = await self.get_bee_run_info(bee_run_uuid)
        print(f"✅ Bee run created: {bee_run_info['created_at']}")
        if bee_run_info['wandb_run_url']:
            print(f"🔗 W&B URL: {bee_run_info['wandb_run_url']}")
        
        # Get task runs
        print("\n2️⃣ Fetching task runs...")
        task_runs = await self.get_task_runs(bee_run_uuid)
        
        # Filter tasks if requested
        if task_filter:
            task_runs = [tr for tr in task_runs if task_filter.lower() in tr['task_name'].lower()]
            print(f"🔍 Filtered to {len(task_runs)} tasks matching task name '{task_filter}'")
        
        # Filter by metric if requested
        if metric_filter:
            filtered_tasks = []
            for tr in task_runs:
                if tr['metrics'] and any(metric_filter.lower() in k.lower() for k in tr['metrics'].keys()):
                    filtered_tasks.append(tr)
            task_runs = filtered_tasks
            print(f"🎯 Filtered to {len(task_runs)} tasks with metric '{metric_filter}'")
        
        # Limit number of tasks if requested
        if max_tasks and len(task_runs) > max_tasks:
            print(f"⚠️  Limiting to first {max_tasks} tasks (out of {len(task_runs)} total)")
            task_runs = task_runs[:max_tasks]
        
        print(f"✅ Found {len(task_runs)} task runs:")
        for i, tr in enumerate(task_runs, 1):
            print(f"   {i}. {tr['task_name']} - {tr['estimator_name']}")
            if tr['metrics']:
                metrics_str = ', '.join([f"{k}={v:.3f}" if v is not None else f"{k}=None" 
                                        for k, v in list(tr['metrics'].items())[:3]])
                print(f"      Metrics: {metrics_str}")
        
        # Download samples for each task run
        print("\n3️⃣ Downloading samples...")
        all_samples = []
        total_samples = 0
        
        for i, task_run in enumerate(task_runs, 1):
            print(f"\n[{i}/{len(task_runs)}] Task: {task_run['task_name']}")
            
            samples = await self.get_samples_for_task(
                UUID(task_run['task_run_id']),
                task_run['task_name'],
                sample_limit=sample_limit
            )
            
            # Add task run context to each sample
            for sample in samples:
                sample['task_run_info'] = {
                    'task_name': task_run['task_name'],
                    'estimator_name': task_run['estimator_name'],
                    'task_metrics': task_run['metrics'],
                    'task_metadata': task_run['task_metadata'],
                }
            
            all_samples.extend(samples)
            total_samples += len(samples)
            print(f"    ✓ {len(samples)} samples downloaded (total: {total_samples})")
        
        # Save to JSONL
        print(f"\n4️⃣ Saving to JSONL...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_run_id = bee_run_id[:8]  # First 8 chars of UUID
        output_file = output_dir / f"bee_run_{safe_run_id}_{timestamp}.jsonl"
        
        with open(output_file, 'w') as f:
            for sample in all_samples:
                f.write(json.dumps(sample, default=str) + '\n')
        
        print(f"✅ Saved {len(all_samples)} samples to: {output_file}")
        
        # Create summary file
        summary = {
            "bee_run_id": bee_run_id,
            "bee_run_info": bee_run_info,
            "task_runs": task_runs,
            "total_samples": len(all_samples),
            "total_tasks": len(task_runs),
            "download_timestamp": timestamp,
            "output_file": str(output_file),
            "environment": self.environment,
        }
        
        summary_file = output_dir / f"bee_run_{safe_run_id}_{timestamp}_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"📝 Summary saved to: {summary_file}")
        
        # Print statistics
        print("\n📊 Download Statistics:")
        print(f"   Total samples: {len(all_samples)}")
        print(f"   Total task runs: {len(task_runs)}")
        
        # Analyze sample metrics
        samples_with_metrics = [s for s in all_samples if s.get('metrics')]
        if samples_with_metrics:
            print(f"   Samples with metrics: {len(samples_with_metrics)}")
            
            # Find common metric names
            all_metric_names = set()
            for sample in samples_with_metrics[:100]:  # Sample first 100
                all_metric_names.update(sample['metrics'].keys())
            
            if all_metric_names:
                print(f"   Metric names found: {', '.join(sorted(list(all_metric_names)[:5]))}")
        
        # Check for outputs with trajectories
        samples_with_outputs = [s for s in all_samples if s.get('outputs')]
        if samples_with_outputs:
            print(f"   Samples with outputs: {len(samples_with_outputs)}")
            
            # Check output structure
            first_output = all_samples[0]['outputs'] if all_samples else {}
            if first_output:
                output_keys = list(first_output.keys()) if isinstance(first_output, dict) else ['<non-dict>']
                print(f"   Output keys: {', '.join(output_keys[:5])}")
        
        print(f"\n✨ Complete! All data saved to {output_dir}")
        
        return summary


async def async_main():
    """Async main CLI function."""
    parser = argparse.ArgumentParser(
        description="Download all samples from a bee run with full metadata and trajectories",
        epilog="Examples:\n"
               "  download-bee-run --run-id 'abc-123-def'\n"
               "  download-bee-run --run-id 'abc-123-def' --output-dir ./my_data\n"
               "  download-bee-run --run-id 'abc-123-def' --task-filter 'tau'",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--run-id", "-r", required=True, help="Bee run ID to download")
    parser.add_argument("--output-dir", "-o", default="./output", help="Output directory for JSONL files (default: ./output)")
    parser.add_argument("--task-filter", "-t", help="Filter tasks by name (substring match)")
    parser.add_argument("--metric-filter", help="Filter tasks by metric name (only download tasks with this metric)")
    parser.add_argument("--task-run-id", help="Download samples from a specific task run ID (bypasses API issues)")
    parser.add_argument("--max-tasks", "-m", type=int, help="Limit number of tasks to download")
    parser.add_argument("--sample-limit", "-s", type=int, help="Limit number of samples per task (useful for large tasks)")
    parser.add_argument("--list-metrics", action="store_true", help="List all tasks and their metrics, then exit")
    parser.add_argument("--list-task-ids", action="store_true", help="List all task run IDs, then exit")
    parser.add_argument("--environment", choices=["production", "staging"], default="production")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    
    downloader = BeeRunDownloader(
        environment=args.environment,
        verbose=args.verbose
    )
    
    try:
        if args.list_metrics or args.list_task_ids:
            # Just list tasks and metrics/IDs
            bee_run_uuid = UUID(args.run_id)
            print(f"🐝 Fetching tasks for bee run: {args.run_id}\n")
            task_runs = await downloader.get_task_runs(bee_run_uuid)
            
            print(f"Found {len(task_runs)} tasks:\n")
            for i, tr in enumerate(task_runs, 1):
                print(f"{i}. {tr['task_name']}")
                if args.list_task_ids:
                    print(f"   Task Run ID: {tr['task_run_id']}")
                if args.list_metrics and tr['metrics']:
                    print(f"   Metrics: {', '.join(tr['metrics'].keys())}")
                elif args.list_metrics:
                    print(f"   Metrics: (none)")
                print()
            return 0
        
        # Handle direct task_run_id download
        if args.task_run_id:
            print(f"📥 Downloading samples from task run: {args.task_run_id}")
            task_run_uuid = UUID(args.task_run_id)
            
            # Get task info first
            task_runs = await downloader.get_task_runs(UUID(args.run_id))
            task_info = next((tr for tr in task_runs if tr['task_run_id'] == args.task_run_id), None)
            
            if not task_info:
                print(f"❌ Task run {args.task_run_id} not found in this bee run")
                return 1
            
            print(f"Task: {task_info['task_name']}")
            print(f"Estimator: {task_info['estimator_name']}")
            
            # Download samples
            samples = await downloader.get_samples_for_task(
                task_run_uuid, 
                task_info['task_name'],
                sample_limit=args.sample_limit
            )
            
            # Save to file
            from datetime import datetime
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_task_name = task_info['task_name'].replace("/", "_").replace(".", "_")[:30]
            output_file = output_dir / f"task_{safe_task_name}_{timestamp}.jsonl"
            
            with open(output_file, 'w') as f:
                for sample in samples:
                    sample['task_run_info'] = {
                        'task_name': task_info['task_name'],
                        'estimator_name': task_info['estimator_name'],
                        'task_metrics': task_info['metrics'],
                    }
                    f.write(json.dumps(sample, default=str) + '\n')
            
            print(f"✅ Saved {len(samples)} samples to: {output_file}")
            return 0
        
        await downloader.download_bee_run(
            bee_run_id=args.run_id,
            output_dir=output_dir,
            task_filter=args.task_filter,
            metric_filter=args.metric_filter,
            max_tasks=args.max_tasks,
            sample_limit=args.sample_limit,
        )
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


def main():
    """Entry point for console script."""
    exit_code = asyncio.run(async_main())
    exit(exit_code)


if __name__ == "__main__":
    main()

