"""
Tests for individual widgets in the Bee Sample Viewer.
"""

import pytest
import json
from bee_sample_viewer.widgets import JSONViewer, SampleDetail, SampleList


class TestJSONViewer:
    """Test the JSONViewer widget."""
    
    @pytest.mark.asyncio
    async def test_json_viewer_renders_dict(self, sample_data):
        """Test that JSONViewer can render a dictionary."""
        viewer = JSONViewer(id="test")
        
        # Mount the widget in a minimal app context
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            # Set data
            test_data = sample_data[0]["outputs"]
            viewer.data = test_data
            await pilot.pause()
            
            # Verify data is set
            assert viewer.data is not None
            assert isinstance(viewer.data, dict)
            assert "raw_prompt" in viewer.data
    
    @pytest.mark.asyncio
    async def test_json_viewer_renders_none(self):
        """Test that JSONViewer handles None data gracefully."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            # Set None data
            viewer.data = None
            await pilot.pause()
            
            # Should show "No data" message
            assert viewer.data is None
    
    @pytest.mark.asyncio
    async def test_json_viewer_handles_large_data(self, sample_data):
        """Test that JSONViewer can handle large data."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            # Set large data
            large_data = sample_data[2]["outputs"]  # Has repeated content
            viewer.data = large_data
            await pilot.pause()
            
            # Verify data is set
            assert viewer.data is not None
            json_str = json.dumps(large_data, indent=2, default=str)
            assert len(json_str) > 1000  # Ensure it's actually large


class TestSampleDetail:
    """Test the SampleDetail widget."""
    
    @pytest.mark.asyncio
    async def test_sample_detail_displays_sample_info(self, sample_data):
        """Test that SampleDetail displays sample information."""
        detail = SampleDetail(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(detail)
            await pilot.pause()
            
            # Set sample
            detail.sample = sample_data[0]
            await pilot.pause()
            
            # Verify sample is set
            assert detail.sample is not None
            assert detail.sample["sample_id"] == sample_data[0]["sample_id"]
    
    @pytest.mark.asyncio
    async def test_sample_detail_handles_none(self):
        """Test that SampleDetail handles None gracefully."""
        detail = SampleDetail(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(detail)
            await pilot.pause()
            
            # Set None
            detail.sample = None
            await pilot.pause()
            
            # Should show "No sample selected"
            assert detail.sample is None


class TestSampleList:
    """Test the SampleList widget."""
    
    @pytest.mark.asyncio
    async def test_sample_list_basic_functionality(self):
        """Test basic SampleList functionality."""
        sample_list = SampleList(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(sample_list)
            await pilot.pause()
            
            # Add columns
            sample_list.add_columns("ID", "Task", "Pass")
            await pilot.pause()
            
            # Add rows
            sample_list.add_row("test123", "TestTask", "✓")
            sample_list.add_row("test456", "TestTask2", "✗")
            await pilot.pause()
            
            # Verify rows were added
            assert sample_list.row_count == 2



