"""Tests for reward explanation viewer."""

import json
import pytest
from bee_sample_viewer.reward_explanation import RewardExplanationViewer


class TestRewardExplanationBasics:
    """Test basic functionality of reward explanation viewer."""
    
    @pytest.mark.asyncio
    async def test_viewer_initializes(self):
        """Test that viewer can be created."""
        viewer = RewardExplanationViewer()
        assert viewer is not None
        assert viewer._current_data is None
    
    @pytest.mark.asyncio
    async def test_viewer_handles_none_data(self):
        """Test viewer with no data."""
        viewer = RewardExplanationViewer()
        viewer.data = None
        # Should not crash
    
    @pytest.mark.asyncio
    async def test_viewer_handles_empty_dict(self):
        """Test viewer with empty dict."""
        viewer = RewardExplanationViewer()
        viewer.data = {}
        # Should not crash


class TestActionFiltering:
    """Test filtering of database-mutating actions."""
    
    def test_filters_respond_actions(self):
        """Test that RESPOND actions are filtered out."""
        viewer = RewardExplanationViewer()
        
        actions = [
            {"name": "get_order", "kwargs": {"order_id": "123"}},
            {"name": "respond", "kwargs": {"content": "Done"}},
            {"name": "update_order", "kwargs": {"order_id": "123"}},
        ]
        
        filtered = viewer._filter_db_actions(actions)
        
        assert len(filtered) == 2
        assert all(a["name"] != "respond" for a in filtered)
    
    def test_filters_case_insensitive(self):
        """Test that filtering is case-insensitive."""
        viewer = RewardExplanationViewer()
        
        actions = [
            {"name": "get_order", "kwargs": {}},
            {"name": "RESPOND", "kwargs": {}},
            {"name": "Respond", "kwargs": {}},
        ]
        
        filtered = viewer._filter_db_actions(actions)
        
        assert len(filtered) == 1
    
    def test_preserves_order(self):
        """Test that action order is preserved."""
        viewer = RewardExplanationViewer()
        
        actions = [
            {"name": "action1", "kwargs": {}},
            {"name": "respond", "kwargs": {}},
            {"name": "action2", "kwargs": {}},
            {"name": "action3", "kwargs": {}},
        ]
        
        filtered = viewer._filter_db_actions(actions)
        
        assert filtered[0]["name"] == "action1"
        assert filtered[1]["name"] == "action2"
        assert filtered[2]["name"] == "action3"


class TestActionComparison:
    """Test action comparison logic."""
    
    def test_actions_match_exact(self):
        """Test that identical actions match."""
        viewer = RewardExplanationViewer()
        
        action1 = {"name": "get_order", "kwargs": {"order_id": "123"}}
        action2 = {"name": "get_order", "kwargs": {"order_id": "123"}}
        
        assert viewer._actions_match(action1, action2)
    
    def test_actions_differ_by_name(self):
        """Test that actions with different names don't match."""
        viewer = RewardExplanationViewer()
        
        action1 = {"name": "get_order", "kwargs": {"order_id": "123"}}
        action2 = {"name": "update_order", "kwargs": {"order_id": "123"}}
        
        assert not viewer._actions_match(action1, action2)
    
    def test_actions_differ_by_kwargs(self):
        """Test that actions with different kwargs don't match."""
        viewer = RewardExplanationViewer()
        
        action1 = {"name": "get_order", "kwargs": {"order_id": "123"}}
        action2 = {"name": "get_order", "kwargs": {"order_id": "456"}}
        
        assert not viewer._actions_match(action1, action2)
    
    def test_actions_match_with_complex_kwargs(self):
        """Test matching with complex kwargs."""
        viewer = RewardExplanationViewer()
        
        action1 = {
            "name": "update", 
            "kwargs": {"ids": [1, 2, 3], "data": {"key": "value"}}
        }
        action2 = {
            "name": "update",
            "kwargs": {"ids": [1, 2, 3], "data": {"key": "value"}}
        }
        
        assert viewer._actions_match(action1, action2)


class TestActionFormatting:
    """Test action formatting for display."""
    
    def test_formats_simple_action(self):
        """Test formatting a simple action."""
        viewer = RewardExplanationViewer()
        
        action = {"name": "get_order", "kwargs": {"order_id": "123"}}
        result = viewer._format_action(action)
        
        # Should contain action name
        assert "get_order" in str(result)
    
    def test_formats_action_with_list(self):
        """Test formatting action with list parameter."""
        viewer = RewardExplanationViewer()
        
        action = {"name": "delete_items", "kwargs": {"ids": [1, 2, 3]}}
        result = viewer._format_action(action)
        
        assert "delete_items" in str(result)
    
    def test_truncates_long_list(self):
        """Test that long lists are truncated."""
        viewer = RewardExplanationViewer()
        
        action = {"name": "delete", "kwargs": {"ids": list(range(100))}}
        result = viewer._format_action(action)
        
        # Should show truncation
        result_str = str(result)
        assert "..." in result_str or "items" in result_str.lower()
    
    def test_truncates_long_string(self):
        """Test that long strings are truncated."""
        viewer = RewardExplanationViewer()
        
        long_string = "x" * 100
        action = {"name": "update", "kwargs": {"data": long_string}}
        result = viewer._format_action(action)
        
        # Should be truncated
        assert len(str(result)) < len(long_string) + 50


class TestRewardExplanationGeneration:
    """Test full reward explanation generation."""
    
    def test_handles_missing_reward_info(self):
        """Test handling samples without reward info."""
        viewer = RewardExplanationViewer()
        
        sample = {
            "metrics": {"mean_reward": 0.0},
            "inputs": {}
        }
        
        # Should not crash
        viewer.data = sample
    
    def test_handles_invalid_json_in_info(self):
        """Test handling invalid JSON in info field."""
        viewer = RewardExplanationViewer()
        
        sample = {
            "metrics": {"mean_reward": 0.0},
            "inputs": {
                "metadata": {
                    "info": "not valid json {"
                }
            }
        }
        
        # Should not crash
        viewer.data = sample
    
    def test_handles_failed_sample(self):
        """Test explanation for failed sample."""
        viewer = RewardExplanationViewer()
        
        info = {
            "task": {
                "instruction": "Cancel order",
                "actions": [{"name": "cancel_order", "kwargs": {"id": "123"}}],
                "outputs": [],
            },
            "reward_info": {
                "reward": 0.0,
                "info": {
                    "r_actions": False,
                    "gt_data_hash": "abc123"
                },
                "actions": [{"name": "cancel_order", "kwargs": {"id": "456"}}]
            }
        }
        
        sample = {
            "metrics": {"mean_reward": 0.0, "expect_no_op": False},
            "inputs": {
                "metadata": {
                    "info": json.dumps(info)
                }
            }
        }
        
        viewer.data = sample
        # Should generate explanation without crashing
    
    def test_handles_passed_sample(self):
        """Test explanation for passed sample."""
        viewer = RewardExplanationViewer()
        
        info = {
            "task": {
                "instruction": "Cancel order",
                "actions": [{"name": "cancel_order", "kwargs": {"id": "123"}}],
                "outputs": [],
            },
            "reward_info": {
                "reward": 1.0,
                "info": {
                    "r_actions": True,
                    "gt_data_hash": "abc123"
                },
                "actions": [{"name": "cancel_order", "kwargs": {"id": "123"}}]
            }
        }
        
        sample = {
            "metrics": {"mean_reward": 1.0, "expect_no_op": False},
            "inputs": {
                "metadata": {
                    "info": json.dumps(info)
                }
            }
        }
        
        viewer.data = sample
        # Should generate explanation without crashing
    
    def test_handles_sample_with_required_outputs(self):
        """Test explanation for sample with required outputs."""
        viewer = RewardExplanationViewer()
        
        info = {
            "task": {
                "instruction": "Find email",
                "actions": [{"name": "get_user", "kwargs": {"id": "123"}}],
                "outputs": ["john@example.com"],
            },
            "reward_info": {
                "reward": 1.0,
                "info": {
                    "r_outputs": 1.0,
                    "outputs": {"john@example.com": True}
                },
                "actions": [{"name": "get_user", "kwargs": {"id": "123"}}]
            }
        }
        
        sample = {
            "metrics": {"mean_reward": 1.0, "expect_no_op": False},
            "inputs": {
                "metadata": {
                    "info": json.dumps(info)
                }
            }
        }
        
        viewer.data = sample
        # Should generate explanation without crashing
    
    def test_handles_no_op_task(self):
        """Test explanation for no-op task."""
        viewer = RewardExplanationViewer()
        
        info = {
            "task": {
                "instruction": "Cancel non-existent order",
                "actions": [],
                "outputs": [],
            },
            "reward_info": {
                "reward": 1.0,
                "info": {
                    "r_actions": True,
                    "gt_data_hash": "unchanged"
                },
                "actions": []
            }
        }
        
        sample = {
            "metrics": {"mean_reward": 1.0, "expect_no_op": True},
            "inputs": {
                "metadata": {
                    "info": json.dumps(info)
                }
            }
        }
        
        viewer.data = sample
        # Should generate explanation without crashing


class TestActionsComparisonTable:
    """Test the actions comparison table generation."""
    
    def test_equal_length_actions(self):
        """Test comparison with equal number of actions."""
        viewer = RewardExplanationViewer()
        
        expected = [
            {"name": "action1", "kwargs": {}},
            {"name": "action2", "kwargs": {}}
        ]
        actual = [
            {"name": "action1", "kwargs": {}},
            {"name": "action2", "kwargs": {}}
        ]
        
        table = viewer._create_actions_comparison(expected, actual)
        # Should not crash
        assert table is not None
    
    def test_more_actual_than_expected(self):
        """Test comparison when agent did extra actions."""
        viewer = RewardExplanationViewer()
        
        expected = [{"name": "action1", "kwargs": {}}]
        actual = [
            {"name": "action1", "kwargs": {}},
            {"name": "action2", "kwargs": {}}
        ]
        
        table = viewer._create_actions_comparison(expected, actual)
        # Should not crash and show extra actions
        assert table is not None
    
    def test_fewer_actual_than_expected(self):
        """Test comparison when agent did fewer actions."""
        viewer = RewardExplanationViewer()
        
        expected = [
            {"name": "action1", "kwargs": {}},
            {"name": "action2", "kwargs": {}}
        ]
        actual = [{"name": "action1", "kwargs": {}}]
        
        table = viewer._create_actions_comparison(expected, actual)
        # Should not crash and show missing actions
        assert table is not None
    
    def test_completely_different_actions(self):
        """Test comparison with completely different actions."""
        viewer = RewardExplanationViewer()
        
        expected = [
            {"name": "action1", "kwargs": {"x": 1}},
            {"name": "action2", "kwargs": {"y": 2}}
        ]
        actual = [
            {"name": "action3", "kwargs": {"z": 3}},
            {"name": "action4", "kwargs": {"w": 4}}
        ]
        
        table = viewer._create_actions_comparison(expected, actual)
        # Should not crash
        assert table is not None

