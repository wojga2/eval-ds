"""Test the Tau2Bench reward viewer."""
import pytest
from bee_sample_viewer.reward_viewer import RewardViewer
from rich.console import Console


class TestRewardViewerBasics:
    """Test basic reward viewer functionality."""
    
    def test_initialization(self):
        """Test that reward viewer initializes correctly."""
        viewer = RewardViewer()
        assert viewer is not None
        assert viewer._current_data is None
    
    def test_empty_data(self):
        """Test viewer with no data."""
        viewer = RewardViewer()
        viewer.data = None
        # Should not crash
        assert viewer.data is None


class TestActionExtraction:
    """Test extracting actions from conversation."""
    
    def test_extracts_single_action(self):
        """Test extracting a single action from conversation."""
        viewer = RewardViewer()
        
        conversation = [
            {
                "role": "User",
                "content": [{"text": "Turn on airplane mode", "content_type": "text"}],
                "tool_calls": None,
            },
            {
                "role": "Chatbot",
                "content": None,
                "tool_calls": [
                    {
                        "name": "toggle_airplane_mode",
                        "parameters": {},
                        "tool_call_id": "call_123"
                    }
                ],
            }
        ]
        
        actions = viewer._extract_actions_from_conversation(conversation)
        
        assert len(actions) == 1
        assert actions[0]['name'] == "toggle_airplane_mode"
        assert actions[0]['parameters'] == {}
    
    def test_extracts_multiple_actions(self):
        """Test extracting multiple actions from conversation."""
        viewer = RewardViewer()
        
        conversation = [
            {
                "role": "Chatbot",
                "content": None,
                "tool_calls": [
                    {
                        "name": "action1",
                        "parameters": {"arg": "value"},
                        "tool_call_id": "call_1"
                    },
                    {
                        "name": "action2",
                        "parameters": {},
                        "tool_call_id": "call_2"
                    }
                ],
            },
            {
                "role": "Chatbot",
                "content": None,
                "tool_calls": [
                    {
                        "name": "action3",
                        "parameters": {"key": 123},
                        "tool_call_id": "call_3"
                    }
                ],
            }
        ]
        
        actions = viewer._extract_actions_from_conversation(conversation)
        
        assert len(actions) == 3
        assert actions[0]['name'] == "action1"
        assert actions[1]['name'] == "action2"
        assert actions[2]['name'] == "action3"
    
    def test_no_actions_in_conversation(self):
        """Test conversation with no tool calls."""
        viewer = RewardViewer()
        
        conversation = [
            {
                "role": "User",
                "content": [{"text": "Hello", "content_type": "text"}],
                "tool_calls": None,
            },
            {
                "role": "Chatbot",
                "content": [{"text": "Hi there", "content_type": "text"}],
                "tool_calls": None,
            }
        ]
        
        actions = viewer._extract_actions_from_conversation(conversation)
        
        assert len(actions) == 0


class TestStatusPanel:
    """Test status panel creation."""
    
    def test_creates_pass_status(self):
        """Test creating status panel for passing sample."""
        viewer = RewardViewer()
        
        panel = viewer._create_status_panel(1.0, {"ENV_ASSERTION": 1})
        assert panel is not None
        
        # Render to string to check content
        console = Console(width=80)
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        
        assert "PASS" in output
        assert "1" in output or "1.0" in output
    
    def test_creates_fail_status(self):
        """Test creating status panel for failing sample."""
        viewer = RewardViewer()
        
        panel = viewer._create_status_panel(0, {"ENV_ASSERTION": 0})
        assert panel is not None
        
        # Render to string to check content
        console = Console(width=80)
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        
        assert "FAIL" in output
        assert "0" in output
    
    def test_includes_metrics(self):
        """Test that status panel includes metrics."""
        viewer = RewardViewer()
        
        metrics = {
            "ENV_ASSERTION": 1,
            "ACTION_MATCH": 0
        }
        
        panel = viewer._create_status_panel(0, metrics)
        
        # Render to string
        console = Console(width=80)
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        
        assert "Env Assertion" in output or "ENV_ASSERTION" in output
        assert "Action Match" in output or "ACTION_MATCH" in output


class TestActionAnalysisPanel:
    """Test action analysis panel."""
    
    def test_creates_action_panel_with_matches(self):
        """Test creating action panel with matching actions."""
        viewer = RewardViewer()
        
        action_checks = [
            {
                "action": {
                    "name": "toggle_airplane_mode",
                    "arguments": {},
                },
                "action_match": True,
                "action_reward": 1
            }
        ]
        
        conversation = [
            {
                "role": "Chatbot",
                "tool_calls": [
                    {"name": "toggle_airplane_mode", "parameters": {}}
                ]
            }
        ]
        
        panel = viewer._create_action_analysis(action_checks, conversation)
        assert panel is not None
        
        # Render to string
        console = Console(width=80)
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        
        assert "toggle_airplane_mode" in output
        assert "Actions Actually Taken" in output
    
    def test_shows_mismatched_actions(self):
        """Test showing actions that didn't match."""
        viewer = RewardViewer()
        
        action_checks = [
            {
                "action": {
                    "name": "expected_action",
                    "arguments": {"key": "value"},
                },
                "action_match": False,
                "action_reward": 0
            }
        ]
        
        conversation = [
            {
                "role": "Chatbot",
                "tool_calls": [
                    {"name": "wrong_action", "parameters": {}}
                ]
            }
        ]
        
        panel = viewer._create_action_analysis(action_checks, conversation)
        
        # Render to string
        console = Console(width=80)
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        
        assert "expected_action" in output
        assert "wrong_action" in output
        assert "No" in output or "✗" in output


class TestNLAssertionsPanel:
    """Test natural language assertions panel."""
    
    def test_creates_nl_panel_with_satisfied(self):
        """Test creating panel with satisfied assertions."""
        viewer = RewardViewer()
        
        nl_assertions = [
            {
                "assertion": "The user should receive a confirmation",
                "satisfied": True,
                "explanation": "Confirmation message was sent"
            }
        ]
        
        panel = viewer._create_nl_assertions_panel(nl_assertions)
        assert panel is not None
        
        # Render to string
        console = Console(width=80)
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        
        assert "confirmation" in output.lower()
        assert "✓" in output
    
    def test_creates_nl_panel_with_unsatisfied(self):
        """Test creating panel with unsatisfied assertions."""
        viewer = RewardViewer()
        
        nl_assertions = [
            {
                "assertion": "The system should notify the admin",
                "satisfied": False,
                "explanation": "No notification was sent"
            }
        ]
        
        panel = viewer._create_nl_assertions_panel(nl_assertions)
        
        # Render to string
        console = Console(width=80)
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        
        assert "admin" in output.lower()
        assert "✗" in output
    
    def test_handles_empty_nl_assertions(self):
        """Test handling empty NL assertions."""
        viewer = RewardViewer()
        
        panel = viewer._create_nl_assertions_panel([])
        assert panel is not None
        
        # Render to string
        console = Console(width=80)
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        
        # Should show message about no assertions
        assert "no natural language" in output.lower()


class TestMetricsPanel:
    """Test reward metrics panel."""
    
    def test_creates_metrics_panel(self):
        """Test creating metrics breakdown panel."""
        viewer = RewardViewer()
        
        metrics = {
            "ENV_ASSERTION": 1,
            "ACTION_MATCH": 0.5
        }
        
        text_info = {
            "env": {"note": "Environment state matches"},
            "action": {"note": "Partial action match"}
        }
        
        panel = viewer._create_metrics_panel(metrics, text_info)
        assert panel is not None
        
        # Render to string
        console = Console(width=80)
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        
        assert "ENV_ASSERTION" in output or "Env Assertion" in output
        assert "1" in output
        assert "0.5" in output
    
    def test_handles_empty_metrics(self):
        """Test handling empty metrics."""
        viewer = RewardViewer()
        
        panel = viewer._create_metrics_panel({}, {})
        assert panel is not None
        
        # Render to string
        console = Console(width=80)
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        
        assert "No metrics" in output or output.strip() == ""


class TestFullRewardExplanation:
    """Test full reward explanation generation."""
    
    def test_generates_full_explanation(self):
        """Test generating complete reward explanation."""
        viewer = RewardViewer()
        
        sample = {
            "outputs": {
                "reward": 0,
                "reward_extras": {
                    "action_checks": [
                        {
                            "action": {
                                "name": "toggle_airplane_mode",
                                "arguments": {},
                            },
                            "action_match": False,
                            "action_reward": 0
                        }
                    ],
                    "nl_assertions": []
                },
                "reward_metrics": {
                    "ENV_ASSERTION": 0
                },
                "reward_text_info": {
                    "env": {"note": "Environment mismatch"}
                },
                "conversation": [
                    {
                        "role": "Chatbot",
                        "tool_calls": [
                            {"name": "wrong_action", "parameters": {}}
                        ]
                    }
                ]
            }
        }
        
        explanation = viewer._generate_explanation(sample)
        assert explanation is not None
        
        # Render to string
        console = Console(width=120)
        with console.capture() as capture:
            console.print(explanation)
        output = capture.get()
        
        # Should contain all major sections
        assert "Overall Status" in output or "FAIL" in output
        assert "toggle_airplane_mode" in output
        assert "wrong_action" in output
    
    def test_handles_missing_reward_data(self):
        """Test handling sample with no reward data."""
        viewer = RewardViewer()
        
        sample = {
            "outputs": {}
        }
        
        explanation = viewer._generate_explanation(sample)
        assert explanation is not None
        
        # Should have error message
        console = Console(width=80)
        with console.capture() as capture:
            console.print(explanation)
        output = capture.get()
        
        assert "No reward information" in output
    
    def test_handles_null_reward_extras(self):
        """Test handling sample where reward_extras is null."""
        viewer = RewardViewer()
        
        sample = {
            "outputs": {
                "reward": 0,
                "reward_extras": None,  # This is null in the actual data
                "reward_metrics": None,
                "reward_text_info": None,
                "conversation": None
            }
        }
        
        # Should not crash
        explanation = viewer._generate_explanation(sample)
        assert explanation is not None
        
        # Should still show status
        console = Console(width=120)
        with console.capture() as capture:
            console.print(explanation)
        output = capture.get()
        
        assert "Overall Status" in output or "FAIL" in output or "0" in output


@pytest.mark.asyncio
async def test_viewer_in_app():
    """Test reward viewer integrated in the app."""
    from textual.app import App
    
    viewer = RewardViewer()
    
    class TestApp(App):
        def compose(self):
            yield viewer
    
    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        
        # Set some sample data
        sample = {
            "outputs": {
                "reward": 1,
                "reward_extras": {
                    "action_checks": [],
                    "nl_assertions": []
                },
                "reward_metrics": {"ENV_ASSERTION": 1},
                "reward_text_info": {},
                "conversation": []
            }
        }
        
        viewer.data = sample
        await pilot.pause()
        
        # Should not crash
        assert viewer.data is not None

