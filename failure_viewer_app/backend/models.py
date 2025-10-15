"""Data models for failure viewer app."""

from typing import Any, Optional
from pydantic import BaseModel


class TurnContent(BaseModel):
    """A single turn in a conversation."""
    speaker: str
    content: Optional[str] = None
    tool_call: Optional[dict[str, Any]] = None
    tool_result: Optional[dict[str, Any]] = None
    thinking: Optional[str] = None


class OpenCoding(BaseModel):
    """Open coding results for a sample."""
    descriptive_summary: str
    failure_point_turn: Optional[int] = None
    detailed_analysis: str
    issues_identified: list[str]
    observations: str
    recommendations: str


class AxialCoding(BaseModel):
    """Axial coding results for a sample."""
    primary_code: str
    secondary_codes: list[str]
    severity: str
    rationale: str


class EvalMetrics(BaseModel):
    """Evaluation metrics from tau2bench."""
    success: bool
    reward: float
    total_reward: Optional[float] = None
    checks: Optional[dict[str, Any]] = None


class TaskSample(BaseModel):
    """A complete task sample with all analysis."""
    sample_id: str
    task_name: Optional[str] = None
    conversation: list[TurnContent]
    eval_metrics: EvalMetrics
    open_coding: OpenCoding
    axial_coding: AxialCoding


class ProjectInfo(BaseModel):
    """Information about an analysis project."""
    name: str
    path: str
    num_samples: int
    num_success: int
    num_failed: int
    axial_codes: list[str]  # Unique list of all primary codes


class FilterParams(BaseModel):
    """Filter parameters for task search."""
    axial_codes: list[str] = []
    pass_fail: Optional[str] = None  # "pass", "fail", or None for all

