"""Test that conversations are correctly loaded from nested context structure."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch


# Mock data matching the actual cmd_reasoning_50 structure with role/content list format
MOCK_NESTED_SAMPLE_NEW_FORMAT = {
    "sample_id": "test-nested-001",
    "success": True,
    "reward": 0.5,
    "context": {
        "sample_id": "test-nested-001",
        "task_name": "Test Nested Task",
        "success": True,
        "reward": 0.5,
        "conversation": [
            {
                "role": "System",
                "content": [{"text": "System instructions", "content_type": "text"}]
            },
            {
                "role": "User",
                "content": [{"text": "Hello, I need help", "content_type": "text"}]
            },
            {
                "role": "Agent",
                "content": [{"text": "I can help you with that.", "content_type": "text"}],
                "thinking": "User needs assistance"
            },
            {
                "role": "Agent",
                "content": None,
                "tool_calls": [
                    {
                        "name": "check_account",
                        "arguments": {"user_id": "123"}
                    }
                ]
            },
            {
                "role": "Tool",
                "content": None,
                "tool_results": [
                    {
                        "status": "active"
                    }
                ]
            },
            {
                "role": "Agent",
                "content": [{"text": "Your account is active.", "content_type": "text"}]
            }
        ]
    },
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

# Mock data with old format (speaker/content string)
MOCK_NESTED_SAMPLE_OLD_FORMAT = {
    "sample_id": "test-nested-002",
    "success": True,
    "reward": 0.5,
    "context": {
        "sample_id": "test-nested-002",
        "task_name": "Test Old Format Task",
        "success": True,
        "reward": 0.5,
        "conversation": [
            {
                "speaker": "user",
                "content": "Hello, I need help"
            },
            {
                "speaker": "assistant",
                "content": "I can help you with that.",
                "thinking": "User needs assistance"
            },
            {
                "speaker": "assistant",
                "tool_call": {
                    "name": "check_account",
                    "arguments": {"user_id": "123"}
                }
            },
            {
                "speaker": "system",
                "tool_result": {
                    "status": "active"
                }
            },
            {
                "speaker": "assistant",
                "content": "Your account is active."
            }
        ]
    },
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
def nested_temp_output_dir():
    """Create a temporary output directory with nested structure mock data"""
    temp_dir = tempfile.mkdtemp()
    outputs_path = Path(temp_dir) / "outputs"
    outputs_path.mkdir()
    
    # Create test project with both formats
    project_dir = outputs_path / "test_nested_project"
    project_dir.mkdir()
    
    # Write mock axial coded file with both new and old format samples
    with open(project_dir / "axial_coded_test.jsonl", "w") as f:
        json.dump(MOCK_NESTED_SAMPLE_NEW_FORMAT, f)
        f.write("\n")
        json.dump(MOCK_NESTED_SAMPLE_OLD_FORMAT, f)
        f.write("\n")
    
    yield outputs_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def nested_client(nested_temp_output_dir):
    """Create a test client with nested structure mock data"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    with patch('routes.OUTPUTS_DIR', nested_temp_output_dir):
        from config import create_app
        import routes
        
        app = create_app()
        
        # Register routes
        app.get("/")(routes.root)
        app.get("/api/health")(routes.health_check)
        app.get("/api/projects")(routes.list_projects)
        app.get("/api/projects/{project_name}")(routes.load_project)
        app.post("/api/projects/{project_name}/filter")(routes.filter_tasks)
        app.get("/api/projects/{project_name}/samples/{sample_id}")(routes.get_sample)
        
        with TestClient(app) as test_client:
            yield test_client


class TestNestedConversation:
    """Tests for loading conversations from nested context structure"""
    
    def test_conversation_loaded_from_context_new_format(self, nested_client):
        """Test that conversation is correctly loaded from context.conversation with new format (role/content list)"""
        response = nested_client.get("/api/projects/test_nested_project")
        assert response.status_code == 200
        
        data = response.json()
        assert "samples" in data
        assert len(data["samples"]) == 2  # Both formats
        
        # Check new format sample (first one)
        sample = data["samples"][0]
        
        # Verify conversation is present and has correct structure
        assert "conversation" in sample
        assert len(sample["conversation"]) == 6  # System, User, Agent, Agent (tool), Tool, Agent
        
        # Check first turn (System with content list)
        assert sample["conversation"][0]["speaker"] == "System"
        assert "System instructions" in sample["conversation"][0]["content"]
        
        # Check user turn
        assert sample["conversation"][1]["speaker"] == "User"
        assert sample["conversation"][1]["content"] == "Hello, I need help"
        
        # Check agent turn with thinking
        assert sample["conversation"][2]["speaker"] == "Agent"
        assert sample["conversation"][2]["content"] == "I can help you with that."
        assert sample["conversation"][2]["thinking"] == "User needs assistance"
        
        # Check tool call turn (tool_calls list)
        assert sample["conversation"][3]["speaker"] == "Agent"
        assert sample["conversation"][3]["tool_call"] is not None
        assert sample["conversation"][3]["tool_call"]["name"] == "check_account"
        
        # Check tool result turn (tool_results list)
        assert sample["conversation"][4]["speaker"] == "Tool"
        assert sample["conversation"][4]["tool_result"] is not None
        
        # Check final turn
        assert sample["conversation"][5]["speaker"] == "Agent"
        assert sample["conversation"][5]["content"] == "Your account is active."
    
    def test_conversation_loaded_from_context_old_format(self, nested_client):
        """Test that conversation works with old format (speaker/content string)"""
        response = nested_client.get("/api/projects/test_nested_project")
        assert response.status_code == 200
        
        data = response.json()
        # Check old format sample (second one)
        sample = data["samples"][1]
        
        # Verify conversation is present
        assert "conversation" in sample
        assert len(sample["conversation"]) == 5
        
        # Check first turn (old format)
        assert sample["conversation"][0]["speaker"] == "user"
        assert sample["conversation"][0]["content"] == "Hello, I need help"
    
    def test_task_name_loaded_from_context(self, nested_client):
        """Test that task_name is correctly loaded from context"""
        response = nested_client.get("/api/projects/test_nested_project")
        assert response.status_code == 200
        
        data = response.json()
        sample = data["samples"][0]
        
        assert sample["task_name"] == "Test Nested Task"
    
    def test_eval_metrics_loaded_from_context(self, nested_client):
        """Test that eval metrics are correctly loaded from context"""
        response = nested_client.get("/api/projects/test_nested_project")
        assert response.status_code == 200
        
        data = response.json()
        sample = data["samples"][0]
        
        assert sample["eval_metrics"]["success"] == True
        assert sample["eval_metrics"]["reward"] == 0.5
    
    def test_conversation_not_empty_both_formats(self, nested_client):
        """Test that conversation is not empty for both formats (primary bug check)"""
        response = nested_client.get("/api/projects/test_nested_project")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check both samples
        for i, sample in enumerate(data["samples"]):
            # This is the key test - conversation should NOT be empty
            assert len(sample["conversation"]) > 0, f"Conversation should not be empty for sample {i}"
    
    def test_conversation_has_multiple_speakers(self, nested_client):
        """Test that conversation has multiple speakers"""
        response = nested_client.get("/api/projects/test_nested_project")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check old format (has user/assistant/system)
        old_format_sample = data["samples"][1]
        speakers = set(turn["speaker"].lower() for turn in old_format_sample["conversation"])
        assert "user" in speakers
        assert "assistant" in speakers or "agent" in speakers
        assert "system" in speakers or "tool" in speakers
    
    def test_all_turn_types_present(self, nested_client):
        """Test that all turn types (content, tool_call, tool_result) are present"""
        response = nested_client.get("/api/projects/test_nested_project")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check across all samples
        all_conversations = []
        for sample in data["samples"]:
            all_conversations.extend(sample["conversation"])
        
        has_content = any(turn.get("content") for turn in all_conversations)
        has_tool_call = any(turn.get("tool_call") for turn in all_conversations)
        has_tool_result = any(turn.get("tool_result") for turn in all_conversations)
        has_thinking = any(turn.get("thinking") for turn in all_conversations)
        
        assert has_content, "Should have at least one turn with content"
        assert has_tool_call, "Should have at least one tool call"
        assert has_tool_result, "Should have at least one tool result"
        assert has_thinking, "Should have at least one turn with thinking"

