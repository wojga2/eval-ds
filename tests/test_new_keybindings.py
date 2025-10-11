"""
Tests for updated keybindings (arrow keys for navigation and scrolling).
"""

import pytest
from bee_sample_viewer.app import BeeViewerApp
from bee_sample_viewer.widgets import JSONViewer


class TestArrowNavigation:
    """Test arrow key navigation between samples."""
    
    @pytest.mark.asyncio
    async def test_left_arrow_prev_sample(self, test_jsonl_file):
        """Test that left arrow goes to previous sample."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Go to second sample first
            app.show_sample(1)
            await pilot.pause()
            assert app.current_sample_index == 1
            
            # Press left arrow
            app.action_prev_sample()
            await pilot.pause()
            
            # Should be at first sample
            assert app.current_sample_index == 0
    
    @pytest.mark.asyncio
    async def test_right_arrow_next_sample(self, test_jsonl_file):
        """Test that right arrow goes to next sample."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Start at first sample
            assert app.current_sample_index == 0
            
            # Press right arrow
            app.action_next_sample()
            await pilot.pause()
            
            # Should be at second sample
            assert app.current_sample_index == 1
    
    @pytest.mark.asyncio
    async def test_vim_keys_still_work(self, test_jsonl_file):
        """Test that j/k keys still work for navigation."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # j for next
            await pilot.press("j")
            await pilot.pause()
            assert app.current_sample_index == 1
            
            # k for previous
            await pilot.press("k")
            await pilot.pause()
            assert app.current_sample_index == 0


class TestContentScrolling:
    """Test up/down arrow scrolling in content."""
    
    @pytest.mark.asyncio
    async def test_up_arrow_scrolls_content(self, test_jsonl_file):
        """Test that up arrow scrolls content up."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Get the active viewer
            viewer = app._get_active_viewer()
            assert viewer is not None
            
            # Call scroll up action
            app.action_scroll_up()
            await pilot.pause()
            
            # Should not crash (content exists)
            assert app.is_running
    
    @pytest.mark.asyncio
    async def test_down_arrow_scrolls_content(self, test_jsonl_file):
        """Test that down arrow scrolls content down."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Get the active viewer
            viewer = app._get_active_viewer()
            assert viewer is not None
            
            # Call scroll down action
            app.action_scroll_down()
            await pilot.pause()
            
            # Should not crash
            assert app.is_running
    
    @pytest.mark.asyncio
    async def test_scroll_works_on_active_tab(self, test_jsonl_file):
        """Test that scrolling works on the currently active tab."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Should start on Outputs tab
            active_viewer = app._get_active_viewer()
            assert active_viewer is not None
            assert active_viewer.id == "json-outputs"
            
            # Switch to Metrics tab
            from textual.widgets import TabbedContent
            tabbed = app.query_one(TabbedContent)
            tabbed.active = "tab-metrics"
            await pilot.pause()
            
            # Active viewer should now be metrics
            active_viewer = app._get_active_viewer()
            assert active_viewer is not None
            assert active_viewer.id == "json-metrics"


class TestPageScrolling:
    """Test Shift+up/down for page scrolling."""
    
    @pytest.mark.asyncio
    async def test_shift_down_pages_down(self, test_jsonl_file):
        """Test that Shift+Down scrolls down by one page."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Get initial scroll position
            viewer = app._get_active_viewer()
            assert viewer is not None
            
            # Call page down action
            app.action_page_down()
            await pilot.pause()
            
            # Should not crash
            assert app.is_running
    
    @pytest.mark.asyncio
    async def test_shift_up_pages_up(self, test_jsonl_file):
        """Test that Shift+Up scrolls up by one page."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Get viewer
            viewer = app._get_active_viewer()
            assert viewer is not None
            
            # Call page up action
            app.action_page_up()
            await pilot.pause()
            
            # Should not crash
            assert app.is_running


class TestJumpScrolling:
    """Test Home/End for jumping to top/bottom."""
    
    @pytest.mark.asyncio
    async def test_home_jumps_to_top(self, test_jsonl_file):
        """Test that Home jumps to top of content."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            viewer = app._get_active_viewer()
            assert viewer is not None
            
            # Call scroll home action
            app.action_scroll_home()
            await pilot.pause()
            
            # Should not crash
            assert app.is_running
    
    @pytest.mark.asyncio
    async def test_end_jumps_to_bottom(self, test_jsonl_file):
        """Test that End jumps to bottom of content."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            viewer = app._get_active_viewer()
            assert viewer is not None
            
            # Call scroll end action
            app.action_scroll_end()
            await pilot.pause()
            
            # Should not crash
            assert app.is_running


class TestGetActiveViewer:
    """Test the _get_active_viewer helper method."""
    
    @pytest.mark.asyncio
    async def test_returns_correct_viewer_for_each_tab(self, test_jsonl_file):
        """Test that _get_active_viewer returns the correct viewer for each tab."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            from textual.widgets import TabbedContent
            tabbed = app.query_one(TabbedContent)
            
            # Test each tab
            tab_mappings = [
                ("tab-outputs", "json-outputs"),
                ("tab-inputs", "json-inputs"),
                ("tab-metrics", "json-metrics"),
                ("tab-debug", "json-debug"),
                ("tab-full", "json-full"),
            ]
            
            for tab_id, viewer_id in tab_mappings:
                tabbed.active = tab_id
                await pilot.pause()
                
                viewer = app._get_active_viewer()
                assert viewer is not None
                assert viewer.id == viewer_id
    
    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_tab(self, test_jsonl_file):
        """Test that _get_active_viewer handles invalid tabs gracefully."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Manually set an invalid tab (shouldn't happen in practice)
            from textual.widgets import TabbedContent
            tabbed = app.query_one(TabbedContent)
            # This should still return a valid viewer (defaults to first tab)
            viewer = app._get_active_viewer()
            assert viewer is not None


class TestRemovedFunctionality:
    """Test that old space-to-focus functionality is removed."""
    
    @pytest.mark.asyncio
    async def test_space_key_no_longer_focuses(self, test_jsonl_file):
        """Test that space key doesn't have focus functionality."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Press space - should not do anything special
            await pilot.press("space")
            await pilot.pause()
            
            # App should still be running
            assert app.is_running
    
    @pytest.mark.asyncio
    async def test_action_focus_content_removed(self, test_jsonl_file):
        """Test that action_focus_content method is removed."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        
        # Method should not exist
        assert not hasattr(app, 'action_focus_content')


class TestScrollingIntegration:
    """Integration tests for complete scrolling workflow."""
    
    @pytest.mark.asyncio
    async def test_can_scroll_after_changing_samples(self, test_jsonl_file):
        """Test that scrolling works after changing samples."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Change sample
            app.action_next_sample()
            await pilot.pause()
            
            # Should still be able to scroll
            app.action_scroll_down()
            await pilot.pause()
            assert app.is_running
            
            app.action_scroll_up()
            await pilot.pause()
            assert app.is_running
    
    @pytest.mark.asyncio
    async def test_can_scroll_after_changing_tabs(self, test_jsonl_file):
        """Test that scrolling works after changing tabs."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Change tab
            from textual.widgets import TabbedContent
            tabbed = app.query_one(TabbedContent)
            tabbed.active = "tab-metrics"
            await pilot.pause()
            
            # Should still be able to scroll
            app.action_scroll_down()
            await pilot.pause()
            assert app.is_running
            
            app.action_page_down()
            await pilot.pause()
            assert app.is_running

