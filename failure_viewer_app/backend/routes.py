"""API routes for failure viewer app."""

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from models import (
    ProjectInfo,
    TaskSample,
    FilterParams,
    TurnContent,
    OpenCoding,
    AxialCoding,
    EvalMetrics,
)

logger = logging.getLogger(__name__)

# Path to failure analysis outputs
OUTPUTS_DIR = Path(__file__).parent.parent.parent / "failure_analysis" / "outputs"


def root():
    """Root endpoint."""
    logger.debug("Root endpoint called")
    return {"message": "Failure Viewer App API", "version": "1.0.0"}


def health_check():
    """Health check endpoint."""
    logger.debug("Health check endpoint called")
    return {"status": "healthy"}


async def list_projects():
    """List all available analysis projects."""
    logger.info("Listing all projects")
    
    try:
        if not OUTPUTS_DIR.exists():
            logger.warning(f"Outputs directory does not exist: {OUTPUTS_DIR}")
            return JSONResponse(content={"projects": []})
        
        projects = []
        for project_dir in OUTPUTS_DIR.iterdir():
            if not project_dir.is_dir():
                continue
            
            logger.debug(f"Processing project directory: {project_dir.name}")
            
            # Find axial coded file
            axial_files = list(project_dir.glob("axial_coded_*.jsonl"))
            if not axial_files:
                logger.debug(f"No axial coded files found in {project_dir.name}")
                continue
            
            axial_file = axial_files[0]
            logger.debug(f"Loading axial coded file: {axial_file.name}")
            
            # Read samples to get project info
            samples = []
            with open(axial_file, 'r') as f:
                for line in f:
                    if line.strip():
                        samples.append(json.loads(line))
            
            if not samples:
                logger.debug(f"No samples found in {axial_file.name}")
                continue
            
            # Calculate statistics
            num_success = sum(1 for s in samples if s.get('success', False))
            num_failed = len(samples) - num_success
            
            # Get unique axial codes
            axial_codes = sorted(set(
                s.get('axial_coding', {}).get('primary_code', '')
                for s in samples
                if s.get('axial_coding', {}).get('primary_code')
            ))
            
            project_info = ProjectInfo(
                name=project_dir.name,
                path=str(project_dir),
                num_samples=len(samples),
                num_success=num_success,
                num_failed=num_failed,
                axial_codes=axial_codes
            )
            
            projects.append(project_info)
            logger.info(f"Added project: {project_dir.name} with {len(samples)} samples")
        
        logger.info(f"Found {len(projects)} projects")
        return JSONResponse(content={"projects": [p.model_dump() for p in projects]})
        
    except Exception as e:
        logger.error(f"Error listing projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")


async def load_project(project_name: str):
    """Load all samples from a project."""
    logger.info(f"Loading project: {project_name}")
    
    try:
        project_dir = OUTPUTS_DIR / project_name
        if not project_dir.exists():
            logger.error(f"Project not found: {project_name}")
            raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")
        
        # Find axial coded file
        axial_files = list(project_dir.glob("axial_coded_*.jsonl"))
        if not axial_files:
            logger.error(f"No axial coded file found in project: {project_name}")
            raise HTTPException(status_code=404, detail="No axial coded file found in project")
        
        axial_file = axial_files[0]
        logger.debug(f"Loading axial coded file: {axial_file.name}")
        
        # Read all samples
        samples = []
        with open(axial_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    sample_data = json.loads(line)
                    
                    # Extract context (conversation might be nested)
                    context = sample_data.get('context', {})
                    
                    # Parse conversation turns (check both top-level and nested in context)
                    conversation = []
                    conversation_data = sample_data.get('conversation', context.get('conversation', []))
                    for turn in conversation_data:
                        # Extract speaker (could be 'speaker' or 'role')
                        speaker = turn.get('speaker', turn.get('role', ''))
                        
                        # Extract content (could be string or list of dicts with 'text')
                        content = turn.get('content')
                        if isinstance(content, list):
                            # Extract text from list of content blocks
                            text_parts = []
                            for block in content:
                                if isinstance(block, dict) and 'text' in block:
                                    text_parts.append(block['text'])
                            content = '\n'.join(text_parts) if text_parts else None
                        
                        # Extract tool calls (could be 'tool_call' or 'tool_calls')
                        tool_call = turn.get('tool_call')
                        if not tool_call:
                            tool_calls_list = turn.get('tool_calls')
                            if tool_calls_list and isinstance(tool_calls_list, list) and len(tool_calls_list) > 0:
                                # Take first tool call if multiple
                                tool_call = tool_calls_list[0]
                        
                        # Extract tool results (could be 'tool_result' or 'tool_results')
                        tool_result = turn.get('tool_result')
                        if not tool_result:
                            tool_results_list = turn.get('tool_results')
                            if tool_results_list and isinstance(tool_results_list, list) and len(tool_results_list) > 0:
                                # Take first tool result if multiple
                                tool_result = tool_results_list[0]
                        
                        turn_content = TurnContent(
                            speaker=speaker,
                            content=content,
                            tool_call=tool_call,
                            tool_result=tool_result,
                            thinking=turn.get('thinking')
                        )
                        conversation.append(turn_content)
                    
                    # Parse eval metrics (check both top-level and context)
                    eval_metrics = EvalMetrics(
                        success=sample_data.get('success', context.get('success', False)),
                        reward=sample_data.get('reward', context.get('reward', 0.0)),
                        total_reward=sample_data.get('total_reward', context.get('total_reward')),
                        checks=sample_data.get('checks', context.get('checks'))
                    )
                    
                    # Parse open coding
                    open_data = sample_data.get('coding', {})
                    open_coding = OpenCoding(
                        descriptive_summary=open_data.get('descriptive_summary', ''),
                        failure_point_turn=open_data.get('failure_point_turn'),
                        detailed_analysis=open_data.get('detailed_analysis', ''),
                        issues_identified=open_data.get('issues_identified', []),
                        observations=open_data.get('observations', ''),
                        recommendations=open_data.get('recommendations', '')
                    )
                    
                    # Parse axial coding
                    axial_data = sample_data.get('axial_coding', {})
                    axial_coding = AxialCoding(
                        primary_code=axial_data.get('primary_code', ''),
                        secondary_codes=axial_data.get('secondary_codes', []),
                        severity=axial_data.get('severity', ''),
                        rationale=axial_data.get('rationale', '')
                    )
                    
                    # Extract task_name (check both top-level and context)
                    task_name = sample_data.get('task_name', context.get('task_name'))
                    
                    task_sample = TaskSample(
                        sample_id=sample_data.get('sample_id', context.get('sample_id', f'unknown_{line_num}')),
                        task_name=task_name,
                        conversation=conversation,
                        eval_metrics=eval_metrics,
                        open_coding=open_coding,
                        axial_coding=axial_coding
                    )
                    
                    samples.append(task_sample)
                    
                except Exception as e:
                    logger.error(f"Error parsing line {line_num} in {axial_file.name}: {e}")
                    continue
        
        logger.info(f"Loaded {len(samples)} samples from project: {project_name}")
        return JSONResponse(content={"samples": [s.model_dump() for s in samples]})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load project: {str(e)}")


async def filter_tasks(project_name: str, filters: FilterParams):
    """Filter tasks based on criteria."""
    logger.info(f"Filtering tasks for project: {project_name} with filters: {filters}")
    
    try:
        # Load project first
        project_data = await load_project(project_name)
        project_dict = json.loads(project_data.body)
        all_samples = project_dict['samples']
        
        # Apply filters
        filtered_samples = []
        for sample in all_samples:
            # Filter by pass/fail
            if filters.pass_fail:
                if filters.pass_fail == "pass" and not sample['eval_metrics']['success']:
                    continue
                if filters.pass_fail == "fail" and sample['eval_metrics']['success']:
                    continue
            
            # Filter by axial codes
            if filters.axial_codes:
                primary_code = sample['axial_coding']['primary_code']
                secondary_codes = sample['axial_coding']['secondary_codes']
                all_codes = [primary_code] + secondary_codes
                
                # Check if any selected code matches
                if not any(code in all_codes for code in filters.axial_codes):
                    continue
            
            filtered_samples.append(sample)
        
        logger.info(f"Filtered {len(filtered_samples)} samples out of {len(all_samples)}")
        return JSONResponse(content={
            "samples": filtered_samples,
            "total": len(filtered_samples)
        })
        
    except Exception as e:
        logger.error(f"Error filtering tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to filter tasks: {str(e)}")


async def get_sample(project_name: str, sample_id: str):
    """Get a specific sample by ID."""
    logger.info(f"Getting sample {sample_id} from project: {project_name}")
    
    try:
        # Load project
        project_data = await load_project(project_name)
        project_dict = json.loads(project_data.body)
        all_samples = project_dict['samples']
        
        # Find sample
        for sample in all_samples:
            if sample['sample_id'] == sample_id:
                logger.info(f"Found sample: {sample_id}")
                return JSONResponse(content={"sample": sample})
        
        logger.error(f"Sample not found: {sample_id}")
        raise HTTPException(status_code=404, detail=f"Sample not found: {sample_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sample: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get sample: {str(e)}")

