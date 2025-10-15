"""Pytest configuration and fixtures for backend tests"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch

# Mock project data
MOCK_PROJECT_DATA = {
    "test_project_1": {
        "bee_run": "bee_run_test1.jsonl",
        "open_coded": "open_coded_test1.jsonl",
        "axial_coded": "axial_coded_test1.jsonl",
    },
    "test_project_2": {
        "bee_run": "bee_run_test2.jsonl",
        "open_coded": "open_coded_test2.jsonl",
        "axial_coded": "axial_coded_test2.jsonl",
    }
}

# Mock complete sample (as stored in axial_coded file)
MOCK_COMPLETE_SAMPLE = {
    "sample_id": "sample-001",
    "task_name": "Test Task 1",
    "conversation": [
        {"speaker": "user", "content": "Hello"},
        {"speaker": "assistant", "content": "Hi there"}
    ],
    "success": True,
    "reward": 1.0,
    "total_reward": 1.0,
    "checks": {"completed": True},
    "coding": {
        "descriptive_summary": "Test summary",
        "failure_point_turn": None,
        "detailed_analysis": "Test analysis",
        "issues_identified": ["Issue 1"],
        "observations": "Test observations",
        "recommendations": "Test recommendations"
    },
    "axial_coding": {
        "primary_code": "tool_error",
        "secondary_codes": ["procedure_gap"],
        "severity": "minor",
        "rationale": "Test rationale"
    }
}


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory with mock data"""
    temp_dir = tempfile.mkdtemp()
    outputs_path = Path(temp_dir) / "outputs"
    outputs_path.mkdir()
    
    # Create mock project directories
    for project_name, files in MOCK_PROJECT_DATA.items():
        project_dir = outputs_path / project_name
        project_dir.mkdir()
        
        # Write mock files (all contain the complete sample)
        with open(project_dir / files["bee_run"], "w") as f:
            json.dump(MOCK_COMPLETE_SAMPLE, f)
            f.write("\n")
        
        with open(project_dir / files["open_coded"], "w") as f:
            json.dump(MOCK_COMPLETE_SAMPLE, f)
            f.write("\n")
        
        with open(project_dir / files["axial_coded"], "w") as f:
            json.dump(MOCK_COMPLETE_SAMPLE, f)
            f.write("\n")
    
    yield outputs_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def client(temp_output_dir):
    """Create a test client with mocked output directory"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    with patch('routes.OUTPUTS_DIR', temp_output_dir):
        from config import create_app
        import routes
        
        app = create_app()
        
        # Register routes (same as in main.py)
        app.get("/")(routes.root)
        app.get("/api/health")(routes.health_check)
        app.get("/api/projects")(routes.list_projects)
        app.get("/api/projects/{project_name}")(routes.load_project)
        app.post("/api/projects/{project_name}/filter")(routes.filter_tasks)
        app.get("/api/projects/{project_name}/samples/{sample_id}")(routes.get_sample)
        
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
def mock_project_name():
    """Return a mock project name"""
    return "test_project_1"


@pytest.fixture
def mock_tasks():
    """Return mock task data"""
    return [
        {
            "sample_id": "sample-001",
            "task_name": "Test Task 1",
            "conversation": [
                {"speaker": "user", "content": "Hello"},
                {"speaker": "assistant", "content": "Hi there"}
            ],
            "eval_metrics": {
                "success": True,
                "reward": 1.0,
                "total_reward": 1.0
            },
            "open_coding": {
                "descriptive_summary": "Test summary",
                "failure_point_turn": None,
                "detailed_analysis": "Test analysis",
                "issues_identified": ["Issue 1"],
                "observations": "Test observations",
                "recommendations": "Test recommendations"
            },
            "axial_coding": {
                "primary_code": "tool_error",
                "secondary_codes": ["procedure_gap"],
                "severity": "minor",
                "rationale": "Test rationale"
            }
        }
    ]

