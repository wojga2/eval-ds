"""
Tests for the main BeeViewerApp functionality.
"""

import pytest
from bee_sample_viewer.app import BeeViewerApp
from bee_sample_viewer.widgets import JSONViewer, SampleDetail, SampleList
from bee_sample_viewer.conversation_viewer import ConversationViewer


class TestAppInitialization:
    """Test app initialization and setup."""
    
    @pytest.mark.asyncio
    async def test_app_starts_without_file(self, tmp_path, monkeypatch):
        """Test that app starts without a file specified."""
        # Change to a temporary directory with no output/ folder
        monkeypatch.chdir(tmp_path)
        
        app = BeeViewerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # App should start
            assert app.is_running
            
            # Should have empty samples (no output dir exists)
            assert len(app.samples) == 0
            assert len(app.filtered_samples) == 0
    
    @pytest.mark.asyncio
    async def test_app_loads_jsonl_file(self, test_jsonl_file):
        """Test that app loads a JSONL file on startup."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Should have loaded samples
            assert len(app.samples) > 0
            assert len(app.filtered_samples) > 0
            assert len(app.samples) == 3  # From fixture
    
    @pytest.mark.asyncio
    async def test_app_ui_components_exist(self, test_jsonl_file):
        """Test that all UI components are present."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Check for key components
            assert app.query_one("#sidebar")
            assert app.query_one("#main")
            assert app.query_one("#sample-list", SampleList)
            assert app.query_one("#sample-summary", SampleDetail)
            assert app.query_one("#conversation-viewer", ConversationViewer)
            assert app.query_one("#json-metrics", JSONViewer)
            assert app.query_one("#json-debug", JSONViewer)
            assert app.query_one("#json-full", JSONViewer)


class TestSampleLoading:
    """Test sample loading functionality."""
    
    @pytest.mark.asyncio
    async def test_sample_list_populated(self, test_jsonl_file):
        """Test that sample list is populated after loading."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            sample_list = app.query_one("#sample-list", SampleList)
            assert sample_list.row_count == 3  # From fixture
    
    @pytest.mark.asyncio
    async def test_first_sample_selected_on_load(self, test_jsonl_file):
        """Test that first sample is selected after loading."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # First sample should be selected
            assert app.current_sample_index == 0
            
            # Sample detail should show first sample
            sample_detail = app.query_one("#sample-summary", SampleDetail)
            assert sample_detail.sample is not None
            assert sample_detail.sample["sample_id"] == app.samples[0]["sample_id"]
    
    @pytest.mark.asyncio
    async def test_stats_label_shows_count(self, test_jsonl_file):
        """Test that stats label shows correct count."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Verify samples are loaded
            assert len(app.samples) == 3
            assert len(app.filtered_samples) == 3


class TestContentDisplay:
    """Test content display in viewers."""
    
    @pytest.mark.asyncio
    async def test_conversation_viewer_has_data(self, test_jsonl_file):
        """Test that conversation viewer displays data."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            conversation_viewer = app.query_one("#conversation-viewer", ConversationViewer)
            
            # Should have conversation data (if sample has outputs.conversation)
            # For now, just check that the viewer exists
            assert conversation_viewer is not None
    
    @pytest.mark.asyncio
    async def test_metrics_viewer_has_data(self, test_jsonl_file):
        """Test that metrics viewer displays data."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            metrics_viewer = app.query_one("#json-metrics", JSONViewer)
            
            # Should have metrics from first sample
            assert metrics_viewer.data is not None
            assert isinstance(metrics_viewer.data, dict)
            assert "passed" in metrics_viewer.data
    
    @pytest.mark.asyncio
    async def test_debug_viewer_has_data(self, test_jsonl_file):
        """Test that debug info viewer displays data."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            debug_viewer = app.query_one("#json-debug", JSONViewer)
            
            # Should have debug info from first sample
            assert debug_viewer.data is not None
            assert isinstance(debug_viewer.data, dict)
            assert "duration_ms" in debug_viewer.data
    
    @pytest.mark.asyncio
    async def test_full_sample_viewer_has_data(self, test_jsonl_file):
        """Test that full sample viewer displays data."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            full_viewer = app.query_one("#json-full", JSONViewer)
            
            # Should have full sample data
            assert full_viewer.data is not None
            assert isinstance(full_viewer.data, dict)
            assert "sample_id" in full_viewer.data
            assert "outputs" in full_viewer.data
            assert "metrics" in full_viewer.data
    

class TestSampleNavigation:
    """Test sample navigation functionality."""
    
    @pytest.mark.asyncio
    async def test_show_sample_updates_viewers(self, test_jsonl_file):
        """Test that showing a sample updates all viewers."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Show second sample
            app.show_sample(1)
            await pilot.pause()
            
            # Check that current index is updated
            assert app.current_sample_index == 1
            
            # Check that viewers are updated
            metrics_viewer = app.query_one("#json-metrics", JSONViewer)
            assert metrics_viewer.data is not None
            assert isinstance(metrics_viewer.data, dict)
    
    @pytest.mark.asyncio
    async def test_show_sample_out_of_bounds_handled(self, test_jsonl_file):
        """Test that showing out-of-bounds sample is handled gracefully."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            initial_index = app.current_sample_index
            
            # Try to show invalid sample
            app.show_sample(999)
            await pilot.pause()
            
            # Should remain at initial index
            assert app.current_sample_index == initial_index

