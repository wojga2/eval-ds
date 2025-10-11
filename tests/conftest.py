"""
Pytest configuration and fixtures for bee_sample_viewer tests.
"""

import json
import pytest
from pathlib import Path
from typing import List, Dict, Any


@pytest.fixture
def sample_data() -> List[Dict[str, Any]]:
    """Create sample test data matching the JSONL schema."""
    return [
        {
            "sample_id": "12c7b09c-7cfb-4e5b-8c99-1a2b3c4d5e6f",
            "task_run_id": "99b8de7c-98dd-417b-9c72-c96afc03dabf",
            "task_name": "BFCLTask.BFCLInternalHandler",
            "created_at": "2025-10-07T20:30:45.123456",
            "prompt_hash": "abc123def456",
            "outputs": {
                "thinking": None,
                "raw_prompt": "# System Preamble\nYou are a helpful assistant.\n\n## Instructions\n```python\ndef example():\n    return 'test'\n```\n\nPlease help with this task.",
                "generations": None,
                "parse_error": None,
                "finish_reasons": None,
                "raw_generations": None,
                "parsed_successfully": True
            },
            "metrics": {
                "passed": 1.0,
                "parse_success": 1.0,
                "accuracy": 0.95
            },
            "debug_info": {
                "duration_ms": 1234,
                "tokens_used": 567,
                "model": "command-r-plus"
            },
            "inputs": None,
            "inputs_metadata": None
        },
        {
            "sample_id": "f60e9d77-1234-5678-9abc-def012345678",
            "task_run_id": "99b8de7c-98dd-417b-9c72-c96afc03dabf",
            "task_name": "BFCLTask.BFCLInternalHandler",
            "created_at": "2025-10-07T20:31:45.123456",
            "prompt_hash": "def456abc789",
            "outputs": {
                "thinking": "Let me analyze this",
                "raw_prompt": "Another test prompt",
                "generations": ["result1", "result2"],
                "parse_error": None,
                "finish_reasons": ["complete"],
                "raw_generations": ["raw1", "raw2"],
                "parsed_successfully": True
            },
            "metrics": {
                "passed": 0.0,
                "parse_success": 1.0,
                "accuracy": 0.85
            },
            "debug_info": {
                "duration_ms": 2345,
                "tokens_used": 890,
                "model": "command-r-plus"
            },
            "inputs": {"test": "input"},
            "inputs_metadata": {"source": "test"}
        },
        {
            "sample_id": "975a0510-aaaa-bbbb-cccc-ddddeeeeeeee",
            "task_run_id": "99b8de7c-98dd-417b-9c72-c96afc03dabf",
            "task_name": "BFCLTask.BFCLInternalHandler",
            "created_at": "2025-10-07T20:32:45.123456",
            "prompt_hash": "ghi789jkl012",
            "outputs": {
                "thinking": None,
                "raw_prompt": "Third test with long content that exceeds viewport height. " * 50,
                "generations": None,
                "parse_error": None,
                "finish_reasons": None,
                "raw_generations": None,
                "parsed_successfully": True
            },
            "metrics": {
                "passed": 1.0,
                "parse_success": 1.0,
                "accuracy": 1.0
            },
            "debug_info": {
                "duration_ms": 1500,
                "tokens_used": 400,
                "model": "command-r-plus"
            },
            "inputs": None,
            "inputs_metadata": None
        }
    ]


@pytest.fixture
def test_jsonl_file(tmp_path, sample_data) -> Path:
    """Create a temporary JSONL file with test data."""
    jsonl_path = tmp_path / "test_samples.jsonl"
    
    with open(jsonl_path, 'w') as f:
        for sample in sample_data:
            f.write(json.dumps(sample) + '\n')
    
    return jsonl_path


@pytest.fixture
def output_dir_with_files(tmp_path, sample_data) -> Path:
    """Create an output directory with multiple JSONL files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create multiple files with different timestamps
    for i in range(3):
        file_path = output_dir / f"task_test_{i}.jsonl"
        with open(file_path, 'w') as f:
            for sample in sample_data[i:i+1]:  # One sample per file
                f.write(json.dumps(sample) + '\n')
    
    return output_dir



