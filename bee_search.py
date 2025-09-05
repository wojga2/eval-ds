#!/usr/bin/env python3
"""
CLI tool for bee run discovery and search.

Provides comprehensive search functionality for bee runs:
- Search by estimator patterns
- Search by task name
- Filter by wandb user
- Browse recent runs
- List available tasks and estimators

Usage:
    python bee_search.py --estimator "command-r" --limit 5
    python bee_search.py --task "hellaswag" --estimator "gpt-4"
    python bee_search.py --recent --user "alice" --limit 10
    python bee_search.py --list-tasks
"""

import argparse
import asyncio
import sys
from typing import Optional, List, Dict
from uuid import UUID
from checkpoint_metadata_client.client import BeeRunClient, TaskRunClient


class BeeSearch:
    """Unified bee run search and discovery tool."""
    
    def __init__(self, environment: str = "production", use_sa: bool = True, verbose: bool = False):
        """Initialize the bee search client."""
        self.bee_client = BeeRunClient(environment=environment, use_sa=use_sa)
        self.task_client = TaskRunClient(environment=environment, use_sa=use_sa)
        self.environment = environment
        
        if not verbose:
            import logging
            for client in (self.bee_client, self.task_client):
                client.logger.setLevel(logging.WARNING)
    
    async def search_by_estimator_pattern(self, pattern: str, limit: int = 20, task_filter: str = "") -> List[Dict]:
        """
        Search for runs by estimator pattern using working API approach.
        
        This is the core search method that actually works reliably.
        """
        print(f"🔍 Searching for runs with estimator pattern: '{pattern}'")
        if task_filter:
            print(f"🎯 Limited to task: '{task_filter}'")
        
        # Get popular task names to search through
        all_tasks = await self.task_client.distinct_task_names()
        
        if task_filter:
            # If task filter specified, only search matching tasks
            search_tasks = [t for t in all_tasks if task_filter.lower() in t.lower()][:10]
        else:
            # Focus on popular/common tasks first for faster results
            popular_patterns = ['hellaswag', 'mmlu', 'gsm8k', 'math', 'hehe', 'reward', 'preference', 
                              'arc', 'truthful', 'human', 'safety', 'winogrande', 'code', 'reasoning']
            
            popular_tasks = []
            other_tasks = []
            
            for task in all_tasks[:200]:  # Limit to first 200 tasks
                task_lower = task.lower()
                if any(p in task_lower for p in popular_patterns):
                    popular_tasks.append(task)
                else:
                    other_tasks.append(task)
            
            # Search popular tasks first, then others
            search_tasks = (popular_tasks + other_tasks)[:50]  # Limit total search
        
        matching_runs = {}  # bee_run_id -> run_info
        
        for i, task_name in enumerate(search_tasks):
            if i % 10 == 0:
                print(f"🔄 Searched {i}/{len(search_tasks)} tasks, found {len(matching_runs)} unique runs...")
            
            if len(matching_runs) >= limit:
                break
                
            try:
                task_runs = await self.task_client.get_by_task_name(task_name)
                
                for task_run in task_runs:
                    if len(matching_runs) >= limit:
                        break
                    
                    # Check if estimator name matches pattern
                    if pattern.lower() in task_run.estimator_name.lower():
                        bee_run_id = str(task_run.bee_run_id)
                        
                        if bee_run_id not in matching_runs:
                            # Try to get full bee run info
                            try:
                                bee_run = await self.bee_client.get_by_id(task_run.bee_run_id)
                                
                                matching_runs[bee_run_id] = {
                                    "bee_run_id": bee_run_id,
                                    "wandb_user": bee_run.wandb_user if bee_run else "unknown",
                                    "created_at": bee_run.created_at if bee_run else task_run.created_at,
                                    "wandb_run_url": bee_run.wandb_run_url if bee_run else None,
                                    "estimator_name": task_run.estimator_name,
                                    "task_name": task_run.task_name,
                                    "status": task_run.task_metadata.get("eval_run_status", "unknown"),
                                    "metrics_sample": list(task_run.metrics.keys())[:3] if task_run.metrics else [],
                                }
                                
                            except Exception:
                                # Use task run info only
                                matching_runs[bee_run_id] = {
                                    "bee_run_id": bee_run_id,
                                    "wandb_user": "unknown",
                                    "created_at": task_run.created_at,
                                    "wandb_run_url": None,
                                    "estimator_name": task_run.estimator_name,
                                    "task_name": task_run.task_name,
                                    "status": task_run.task_metadata.get("eval_run_status", "unknown"),
                                    "metrics_sample": list(task_run.metrics.keys())[:3] if task_run.metrics else [],
                                }
                                
            except Exception:
                # Skip tasks that fail
                continue
        
        return list(matching_runs.values())
    
    async def search_by_task_name(self, task_name: str, estimator_filter: str = "", limit: int = 10) -> List[Dict]:
        """Search within a specific task, optionally filtering by estimator pattern."""
        print(f"🔍 Searching task '{task_name}'")
        if estimator_filter:
            print(f"🤖 Filtering by estimator pattern: '{estimator_filter}'")
        
        try:
            task_runs = await self.task_client.get_by_task_name(task_name)
            
            matching_runs = {}
            
            for task_run in task_runs:
                # Filter by estimator pattern if provided
                if estimator_filter and estimator_filter.lower() not in task_run.estimator_name.lower():
                    continue
                
                bee_run_id = str(task_run.bee_run_id)
                
                if bee_run_id not in matching_runs:
                    try:
                        bee_run = await self.bee_client.get_by_id(task_run.bee_run_id)
                        
                        matching_runs[bee_run_id] = {
                            "bee_run_id": bee_run_id,
                            "wandb_user": bee_run.wandb_user if bee_run else "unknown",
                            "created_at": bee_run.created_at if bee_run else task_run.created_at,
                            "wandb_run_url": bee_run.wandb_run_url if bee_run else None,
                            "estimator_name": task_run.estimator_name,
                            "task_name": task_run.task_name,
                            "status": task_run.task_metadata.get("eval_run_status", "unknown"),
                            "metrics_sample": list(task_run.metrics.keys())[:3] if task_run.metrics else [],
                        }
                        
                    except Exception:
                        # Use task run info only
                        matching_runs[bee_run_id] = {
                            "bee_run_id": bee_run_id,
                            "wandb_user": "unknown",
                            "created_at": task_run.created_at,
                            "wandb_run_url": None,
                            "estimator_name": task_run.estimator_name,
                            "task_name": task_run.task_name,
                            "status": task_run.task_metadata.get("eval_run_status", "unknown"),
                            "metrics_sample": list(task_run.metrics.keys())[:3] if task_run.metrics else [],
                        }
            
            return list(matching_runs.values())[:limit]
            
        except Exception as e:
            print(f"❌ Error searching task: {e}")
            return []
    
    async def get_recent_runs(self, limit: int = 20, user_filter: str = "", task_hint: str = "") -> List[Dict]:
        """Get recent runs, with optional user filtering using task run approach."""
        print(f"🔍 Finding recent runs...")
        if user_filter:
            print(f"👤 Filtering by user: '{user_filter}'")
        
        # Since direct recent runs API is unreliable, use task-based approach
        all_tasks = await self.task_client.distinct_task_names()
        
        # If we have a task hint, prioritize tasks that match it
        if task_hint:
            print(f"🎯 Prioritizing tasks matching: '{task_hint}'")
            # Find tasks that match the hint
            matching_tasks = [t for t in all_tasks if task_hint.lower() in t.lower()]
            # Take first 50 tasks alphabetically for general coverage, then add matching tasks
            general_tasks = [t for t in all_tasks[:50] if t not in matching_tasks]
            popular_tasks = matching_tasks + general_tasks
            popular_tasks = popular_tasks[:100]  # Expand search scope
        else:
            # Get recent runs from more popular tasks (expanded from 20 to 50)
            popular_tasks = [t for t in all_tasks[:50]]
        
        recent_runs = {}
        
        for task_name in popular_tasks:
            if len(recent_runs) >= limit:
                break
                
            try:
                task_runs = await self.task_client.get_by_task_name(task_name)
                
                # Sort by creation date and take most recent
                task_runs = sorted(task_runs, key=lambda x: x.created_at, reverse=True)
                
                for task_run in task_runs[:5]:  # Top 5 recent per task
                    if len(recent_runs) >= limit:
                        break
                    
                    bee_run_id = str(task_run.bee_run_id)
                    
                    if bee_run_id not in recent_runs:
                        try:
                            bee_run = await self.bee_client.get_by_id(task_run.bee_run_id)
                            
                            # Filter by user if specified
                            if user_filter and bee_run and user_filter.lower() not in (bee_run.wandb_user or "").lower():
                                continue
                            
                            recent_runs[bee_run_id] = {
                                "bee_run_id": bee_run_id,
                                "wandb_user": bee_run.wandb_user if bee_run else "unknown",
                                "created_at": bee_run.created_at if bee_run else task_run.created_at,
                                "wandb_run_url": bee_run.wandb_run_url if bee_run else None,
                                "estimator_name": task_run.estimator_name,
                                "task_name": task_run.task_name,
                                "status": task_run.task_metadata.get("eval_run_status", "unknown"),
                                "metrics_sample": list(task_run.metrics.keys())[:3] if task_run.metrics else [],
                                "tasks": [task_run.task_name],  # For compatibility
                                "estimators": [task_run.estimator_name],
                            }
                            
                        except Exception:
                            continue
            except Exception:
                continue
        
        # Sort by creation date
        runs_list = list(recent_runs.values())
        runs_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return runs_list[:limit]
    
    async def get_available_tasks(self) -> List[str]:
        """Get list of available task names."""
        try:
            tasks = await self.task_client.distinct_task_names()
            return sorted(tasks)
        except Exception as e:
            print(f"❌ Error getting task names: {e}")
            return []
    
    async def get_available_estimators(self) -> List[str]:
        """Get list of available estimator names."""
        try:
            estimators = await self.task_client.distinct_estimator_names()
            return sorted(estimators)
        except Exception as e:
            print(f"❌ Error getting estimator names: {e}")
            return []
    
    async def get_run_by_id(self, bee_run_id: str) -> Dict:
        """Get detailed info for a specific bee run ID."""
        try:
            bee_run = await self.bee_client.get_by_id(UUID(bee_run_id))
            if bee_run:
                return {
                    "bee_run_id": str(bee_run.id),
                    "wandb_user": bee_run.wandb_user,
                    "created_at": bee_run.created_at,
                    "updated_at": getattr(bee_run, 'updated_at', bee_run.created_at),
                    "wandb_run_url": bee_run.wandb_run_url,
                    "wandb_run_id": getattr(bee_run, 'wandb_run_id', None),
                    "tasks": list(bee_run.config.get("tasks", {}).keys()) if hasattr(bee_run, 'config') else [],
                    "estimators": list(bee_run.config.get("estimators", {}).keys()) if hasattr(bee_run, 'config') else [],
                }
            return {}
        except Exception as e:
            print(f"❌ Error loading run: {e}")
            return {}
    
    def print_results(self, runs: List[Dict], title: str = "Search Results"):
        """Print search results in a formatted table."""
        if not runs:
            print(f"📋 {title}: No runs found")
            return
            
        print(f"\n📋 {title} ({len(runs)} found):")
        print("=" * 100)
        
        for i, run in enumerate(runs, 1):
            status_emoji = {"success": "✅", "failed": "❌", "running": "🔄"}.get(run.get("status", "unknown"), "❓")
            
            print(f"{i:2d}. 🐝 {run['bee_run_id']} {status_emoji}")
            print(f"     👤 User: {run.get('wandb_user', 'unknown')}")
            print(f"     📅 Created: {run.get('created_at', 'unknown')}")
            
            if run.get('estimator_name'):
                print(f"     🤖 Estimator: {run['estimator_name']}")
            elif run.get('estimators'):
                est_str = ', '.join(run['estimators'][:2])
                if len(run['estimators']) > 2:
                    est_str += f"... (+{len(run['estimators'])-2} more)"
                print(f"     🤖 Estimators: {est_str}")
            
            if run.get('task_name'):
                print(f"     📊 Task: {run['task_name']}")
            elif run.get('tasks'):
                tasks_str = ', '.join(run['tasks'][:3])
                if len(run['tasks']) > 3:
                    tasks_str += f"... (+{len(run['tasks'])-3} more)"
                print(f"     📊 Tasks: {tasks_str}")
                
            if run.get('wandb_run_url'):
                print(f"     🔗 W&B: {run['wandb_run_url']}")
                
            if run.get('metrics_sample'):
                metrics_str = ', '.join(run['metrics_sample'])
                print(f"     📈 Metrics: {metrics_str}...")
                
            print()
    


async def main():
    """Main CLI function for bee run search and discovery."""
    parser = argparse.ArgumentParser(
        description="CLI tool for bee run search and discovery",
        epilog="Examples: --estimator 'command-r' --limit 5 | --recent --estimator 'command-a' --task 'IFEval' | --estimator 'gpt' --task 'hellaswag' --user 'alice'"
    )
    
    # Search filters
    parser.add_argument("--estimator", "-e", help="Search by estimator pattern")
    parser.add_argument("--task", "-t", help="Search by task name")
    parser.add_argument("--user", "-u", help="Filter by wandb user")
    parser.add_argument("--recent", action="store_true", help="Show recent runs")
    
    # Options  
    parser.add_argument("--limit", "-l", type=int, default=10, help="Limit number of results")
    parser.add_argument("--environment", choices=["production", "staging"], default="production")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Lists
    parser.add_argument("--list-tasks", action="store_true", help="List available tasks")
    parser.add_argument("--list-estimators", action="store_true", help="List available estimators")
    parser.add_argument("--get-run", help="Get details for specific bee run ID")
    
    args = parser.parse_args()
    
    # Check if any search criteria provided
    search_args = [args.estimator, args.task, args.user, args.recent, 
                   args.list_tasks, args.list_estimators, args.get_run]
    if not any(search_args):
        print("❌ Please specify a search criteria. Use --help to see all options.")
        parser.print_help()
        return
    
    # Initialize search client
    search = BeeSearch(environment=args.environment, verbose=args.verbose)
    
    try:
        if args.list_tasks:
            print("🔄 Loading available tasks...")
            tasks = await search.get_available_tasks()
            print(f"\n📊 Available Tasks ({len(tasks)} total):")
            for i, task in enumerate(tasks, 1):
                print(f"  {i:4d}. {task}")
            print(f"\n✨ Showing all {len(tasks)} tasks")
                
        elif args.list_estimators:
            print("🔄 Loading popular estimators...")
            estimators = await search.get_available_estimators()
            
            # Show popular ones first, then others
            popular_patterns = ['command-r', 'gpt-', 'claude-', 'gemini', 'llama', 'mistral']
            popular = [e for e in estimators[:500] if any(p in e.lower() for p in popular_patterns)]
            other = [e for e in estimators[:500] if not any(p in e.lower() for p in popular_patterns)]
            
            # Combine popular first, then others, up to limit
            shown = (popular + other)[:args.limit]
            
            print(f"\n🤖 Estimators ({len(shown)} shown, {len(estimators)} total):")
            for i, est in enumerate(shown, 1):
                marker = "⭐" if any(p in est.lower() for p in popular_patterns) else "  "
                print(f"  {i:2d}. {marker} {est}")
            
            if len(popular) > 0:
                print(f"\n⭐ Found {len(popular)} popular models (marked with ⭐)")
            if args.verbose and len(estimators) > args.limit:
                print(f"💡 Use --limit to see more results (total: {len(estimators)})")
                
        elif args.get_run:
            run_info = await search.get_run_by_id(args.get_run)
            if run_info:
                search.print_results([run_info], "Bee Run Details")
            else:
                print(f"❌ No run found with ID: {args.get_run}")
                
        elif args.recent:
            # Get recent runs, optionally filtered by user, estimator, and/or task
            # Pass task hint to improve search scope
            all_recent = await search.get_recent_runs(
                # This sets the limit for the number of recent runs to fetch.
                # It multiplies the user-specified limit by 10 to retrieve more runs up front,
                # allowing for additional filtering (by estimator/task) before displaying the final results.
                limit=args.limit * 10,
                user_filter=args.user or "", 
                task_hint=args.task or ""
            )
            runs = all_recent
            
            # Apply estimator filter if specified
            if args.estimator:
                runs = [run for run in runs if args.estimator.lower() in run.get('estimator_name', '').lower()]
            
            # Apply task filter if specified  
            if args.task:
                runs = [run for run in runs if args.task.lower() in run.get('task_name', '').lower()]
            
            # Limit final results
            runs = runs[:args.limit]
            
            # Build title
            title = "Recent runs"
            filters = []
            if args.estimator:
                filters.append(f"estimator: {args.estimator}")
            if args.task:
                filters.append(f"task: {args.task}")
            if args.user:
                filters.append(f"user: {args.user}")
            if filters:
                title += f" ({', '.join(filters)})"
                
            search.print_results(runs, title)
            
        elif args.estimator and args.task:
            # Search by both estimator and task
            runs = await search.search_by_estimator_pattern(args.estimator, args.limit, args.task)
            title = f"Runs with estimator: {args.estimator} (task: {args.task})"
            search.print_results(runs, title)
            
        elif args.estimator:
            # Search by estimator only
            runs = await search.search_by_estimator_pattern(args.estimator, args.limit, "")
            title = f"Runs with estimator: {args.estimator}"
            search.print_results(runs, title)
            
        elif args.task:
            # Search by task, optionally filtered by estimator  
            estimator_filter = args.estimator or ""
            runs = await search.search_by_task_name(args.task, estimator_filter, args.limit)
            title = f"Runs for task: {args.task}"
            if estimator_filter:
                title += f" (estimator: {estimator_filter})"
            search.print_results(runs, title)
            
        elif args.user:
            runs = await search.get_recent_runs(limit=args.limit * 2, user_filter=args.user)
            search.print_results(runs[:args.limit], f"Recent runs by user: {args.user}")
            
        else:
            print("❌ Please specify a search criteria. Use --help to see all options.")
            parser.print_help()
            
        # Show usage tip for successful searches
        if 'runs' in locals() and runs:
            print(f"\n💡 Found {len(runs)} matching runs!")
            print("📝 Copy any bee_run_id above for analysis:")
            print(f"   BEE_RUN_ID = '{runs[0]['bee_run_id']}'")
            
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())