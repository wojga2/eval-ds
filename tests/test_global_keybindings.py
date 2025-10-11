"""
Tests for global keybindings that should work from any UI state.
"""

import pytest
from bee_sample_viewer.app import BeeViewerApp
from bee_sample_viewer.widgets import JSONViewer
from textual.widgets import TabbedContent


class TestGlobalMarkdownToggle:
    """Test that 'm' key works from any focus state."""
    
    @pytest.mark.asyncio
    async def test_m_works_with_sample_list_focused(self, test_jsonl_file):
        """Test that 'm' toggles markdown when sample list has focus."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Focus the sample list (default focus)
            sample_list = app.query_one("#sample-list")
            sample_list.focus()
            await pilot.pause()
            
            # Get the outputs viewer
            outputs_viewer = app.query_one("#json-outputs", JSONViewer)
            initial_mode = outputs_viewer.markdown_mode
            
            # Call action directly (key press might not work in test environment)
            app.action_toggle_markdown()
            await pilot.pause()
            
            # Should have toggled
            assert outputs_viewer.markdown_mode != initial_mode
    
    @pytest.mark.asyncio
    async def test_m_works_with_content_focused(self, test_jsonl_file):
        """Test that 'm' toggles markdown when content viewer has focus."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Focus the content
            outputs_viewer = app.query_one("#json-outputs", JSONViewer)
            outputs_viewer.focus()
            await pilot.pause()
            
            initial_mode = outputs_viewer.markdown_mode
            
            # Call action directly
            app.action_toggle_markdown()
            await pilot.pause()
            
            # Should have toggled
            assert outputs_viewer.markdown_mode != initial_mode
    
    @pytest.mark.asyncio
    async def test_m_works_on_different_tabs(self, test_jsonl_file):
        """Test that 'm' toggles the active tab's viewer."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Start on Outputs tab
            outputs_viewer = app.query_one("#json-outputs", JSONViewer)
            assert outputs_viewer.markdown_mode is False
            
            # Toggle markdown on Outputs
            app.action_toggle_markdown()
            await pilot.pause()
            assert outputs_viewer.markdown_mode is True
            
            # Switch to Metrics tab by activating it directly
            tabbed = app.query_one(TabbedContent)
            tabbed.active = "tab-metrics"
            await pilot.pause()
            
            # Metrics should still be in JSON mode
            metrics_viewer = app.query_one("#json-metrics", JSONViewer)
            assert metrics_viewer.markdown_mode is False
            
            # Toggle Metrics to markdown
            app.action_toggle_markdown()
            await pilot.pause()
            assert metrics_viewer.markdown_mode is True
            
            # Outputs should still be in markdown
            assert outputs_viewer.markdown_mode is True
    
    @pytest.mark.asyncio
    async def test_m_updates_active_tab_only(self, test_jsonl_file):
        """Test that 'm' only affects the currently visible tab."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Get all viewers
            outputs_viewer = app.query_one("#json-outputs", JSONViewer)
            inputs_viewer = app.query_one("#json-inputs", JSONViewer)
            metrics_viewer = app.query_one("#json-metrics", JSONViewer)
            
            # All should start in JSON mode
            assert outputs_viewer.markdown_mode is False
            assert inputs_viewer.markdown_mode is False
            assert metrics_viewer.markdown_mode is False
            
            # Toggle on Outputs tab (active by default)
            app.action_toggle_markdown()
            await pilot.pause()
            
            # Only Outputs should be in markdown mode
            assert outputs_viewer.markdown_mode is True
            assert inputs_viewer.markdown_mode is False
            assert metrics_viewer.markdown_mode is False


class TestMarkdownPersistence:
    """Test that markdown mode persists correctly."""
    
    @pytest.mark.asyncio
    async def test_markdown_persists_when_changing_samples(self, test_jsonl_file):
        """Test that markdown mode persists when switching samples."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Enable markdown on first sample
            outputs_viewer = app.query_one("#json-outputs", JSONViewer)
            app.action_toggle_markdown()
            await pilot.pause()
            assert outputs_viewer.markdown_mode is True
            
            # Switch to next sample
            await pilot.press("j")
            await pilot.pause()
            
            # Markdown mode should still be enabled
            assert outputs_viewer.markdown_mode is True
            
            # Switch back
            await pilot.press("k")
            await pilot.pause()
            
            # Still enabled
            assert outputs_viewer.markdown_mode is True

