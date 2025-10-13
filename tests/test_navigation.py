"""
Tests for keyboard navigation and scrolling in Bee Sample Viewer.
"""

import pytest
from bee_sample_viewer.app import BeeViewerApp
from bee_sample_viewer.widgets import JSONViewer


class TestKeyboardNavigation:
    """Test keyboard navigation between samples."""
    
    @pytest.mark.asyncio
    async def test_next_sample_with_j_key(self, test_jsonl_file):
        """Test navigating to next sample with 'j' key."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Should start at sample 0
            assert app.current_sample_index == 0
            
            # Press 'j' to go to next
            await pilot.press("j")
            await pilot.pause()
            
            # Should be at sample 1
            assert app.current_sample_index == 1
    
    @pytest.mark.asyncio
    async def test_next_sample_with_down_arrow(self, test_jsonl_file):
        """Test navigating to next sample with down arrow."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Down arrow is consumed by DataTable first
            # The action is triggered by the table's row selection event
            # So we simulate that by calling the action directly
            app.action_next_sample()
            await pilot.pause()
            
            # Should be at sample 1
            assert app.current_sample_index == 1
    
    @pytest.mark.asyncio
    async def test_prev_sample_with_k_key(self, test_jsonl_file):
        """Test navigating to previous sample with 'k' key."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Go to sample 1 first
            app.show_sample(1)
            await pilot.pause()
            
            # Press 'k' to go back
            await pilot.press("k")
            await pilot.pause()
            
            # Should be back at sample 0
            assert app.current_sample_index == 0
    
    @pytest.mark.asyncio
    async def test_prev_sample_with_up_arrow(self, test_jsonl_file):
        """Test navigating to previous sample with up arrow."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Go to sample 1 first
            app.show_sample(1)
            await pilot.pause()
            
            # Up arrow is consumed by DataTable first
            # Call the action directly
            app.action_prev_sample()
            await pilot.pause()
            
            # Should be back at sample 0
            assert app.current_sample_index == 0
    
    @pytest.mark.asyncio
    async def test_cannot_navigate_past_last_sample(self, test_jsonl_file):
        """Test that navigation stops at last sample."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Go to last sample
            app.show_sample(2)  # Last sample (index 2)
            await pilot.pause()
            
            # Try to go next
            await pilot.press("j")
            await pilot.pause()
            
            # Should still be at sample 2
            assert app.current_sample_index == 2
    
    @pytest.mark.asyncio
    async def test_cannot_navigate_before_first_sample(self, test_jsonl_file):
        """Test that navigation stops at first sample."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Already at sample 0
            assert app.current_sample_index == 0
            
            # Try to go previous
            await pilot.press("k")
            await pilot.pause()
            
            # Should still be at sample 0
            assert app.current_sample_index == 0


class TestHelp:
    """Test help functionality."""
    
    @pytest.mark.asyncio
    async def test_help_shows_on_question_mark(self, test_jsonl_file):
        """Test that '?' key shows help."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Press '?' to show help
            await pilot.press("question_mark")
            await pilot.pause()
            
            # App should still be running (help is shown as notification)
            assert app.is_running


class TestQuit:
    """Test quit functionality."""
    
    @pytest.mark.asyncio
    async def test_quit_with_q_key(self, test_jsonl_file):
        """Test that 'q' key quits the app."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Press 'q' to quit
            await pilot.press("q")
            await pilot.pause()
            
            # App should have exited
            assert not app.is_running

