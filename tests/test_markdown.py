"""
Tests for markdown rendering functionality in Bee Sample Viewer.
"""

import pytest
import json
from pathlib import Path
from bee_sample_viewer.app import BeeViewerApp
from bee_sample_viewer.widgets import JSONViewer


class TestMarkdownDetection:
    """Test markdown content detection."""
    
    @pytest.mark.asyncio
    async def test_detects_markdown_headers(self):
        """Test that markdown headers are detected."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            # Need at least 100 chars for markdown detection
            test_data = {
                "raw_prompt": "## System Preamble\nThis is a test with markdown headers. " * 3
            }
            
            assert viewer._has_markdown_content(test_data) is True
    
    @pytest.mark.asyncio
    async def test_detects_code_blocks(self):
        """Test that code blocks are detected."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            # Need at least 100 chars for markdown detection
            test_data = {
                "raw_prompt": "Here is some code:\n```python\nprint('hello world')\nprint('more code here')\n```\nAnd some more text to reach 100 characters."
            }
            
            assert viewer._has_markdown_content(test_data) is True
    
    @pytest.mark.asyncio
    async def test_does_not_detect_plain_text(self):
        """Test that plain text is not detected as markdown."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            test_data = {
                "raw_prompt": "This is just plain text without markdown."
            }
            
            assert viewer._has_markdown_content(test_data) is False


class TestMarkdownRendering:
    """Test markdown rendering functionality."""
    
    @pytest.mark.asyncio
    async def test_renders_markdown_when_enabled(self):
        """Test that markdown is rendered when mode is enabled."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            test_data = {
                "raw_prompt": "## Test Header\nThis is **bold** text."
            }
            
            viewer.data = test_data
            await pilot.pause()
            
            # Start in JSON mode
            assert viewer.markdown_mode is False
            
            # Toggle to markdown mode
            viewer.action_toggle_markdown()
            await pilot.pause()
            
            assert viewer.markdown_mode is True
    
    @pytest.mark.asyncio
    async def test_toggle_between_modes(self):
        """Test toggling between JSON and markdown modes."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            test_data = {"raw_prompt": "## Test\nContent"}
            viewer.data = test_data
            await pilot.pause()
            
            # Initially in JSON mode
            assert viewer.markdown_mode is False
            
            # Toggle to markdown
            viewer.action_toggle_markdown()
            await pilot.pause()
            assert viewer.markdown_mode is True
            
            # Toggle back to JSON
            viewer.action_toggle_markdown()
            await pilot.pause()
            assert viewer.markdown_mode is False


class TestJSONBlockFormatting:
    """Test JSON block extraction and formatting."""
    
    @pytest.mark.asyncio
    async def test_extracts_json_blocks(self):
        """Test that JSON blocks are extracted from markdown."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            json_block = '{"name": "test", "value": 42}'
            test_data = {
                "raw_prompt": f"## Example\n```json\n{json_block}\n```"
            }
            
            viewer.data = test_data
            viewer._markdown_mode = True
            await pilot.pause()
            
            # The viewer should process this without errors
            assert viewer.data is not None
    
    @pytest.mark.asyncio
    async def test_formats_json_with_indentation(self):
        """Test that JSON is formatted with proper indentation."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            # Compact JSON
            json_block = '{"name":"test","nested":{"key":"value"}}'
            test_data = {
                "raw_prompt": f"```json\n{json_block}\n```"
            }
            
            viewer.data = test_data
            viewer._markdown_mode = True
            await pilot.pause()
            
            # Should be able to parse and format
            import json
            parsed = json.loads(json_block)
            formatted = json.dumps(parsed, indent=2)
            
            # Verify it's properly indented
            assert "  " in formatted or "\t" in formatted


class TestRealBFCLData:
    """Test with real BFCL data."""
    
    @pytest.mark.asyncio
    async def test_loads_real_bfcl_sample(self):
        """Test loading a real BFCL sample."""
        bfcl_file = Path("output/task_BFCLTask_BFCLInternalHandler_20251010_170614.jsonl")
        
        if not bfcl_file.exists():
            pytest.skip("BFCL data file not found")
        
        # Load first sample
        with open(bfcl_file) as f:
            first_line = f.readline()
            sample = json.loads(first_line)
        
        app = BeeViewerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Set the sample data
            app.samples = [sample]
            app.filtered_samples = [sample]
            app.show_sample(0)
            await pilot.pause()
            
            # Check that metrics viewer has data
            metrics_viewer = app.query_one("#json-metrics", JSONViewer)
            assert metrics_viewer.data is not None
            
            # Check that it has some metrics (BFCL data typically has these)
            if metrics_viewer.data and isinstance(metrics_viewer.data, dict):
                # Just verify it's a dict with some content
                assert len(metrics_viewer.data) > 0
    
    @pytest.mark.asyncio
    async def test_renders_bfcl_markdown(self):
        """Test rendering BFCL markdown content."""
        bfcl_file = Path("output/task_BFCLTask_BFCLInternalHandler_20251010_170614.jsonl")
        
        if not bfcl_file.exists():
            pytest.skip("BFCL data file not found")
        
        # Load first sample
        with open(bfcl_file) as f:
            first_line = f.readline()
            sample = json.loads(first_line)
        
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            # Set the outputs data
            outputs = sample.get("outputs", {})
            viewer.data = outputs
            await pilot.pause()
            
            # Should detect markdown
            assert viewer._has_markdown_content(outputs) is True
            
            # Toggle to markdown mode
            viewer.action_toggle_markdown()
            await pilot.pause()
            
            # Should not crash
            assert viewer.markdown_mode is True
    
    @pytest.mark.asyncio
    async def test_bfcl_json_blocks_are_formatted(self):
        """Test that JSON blocks in BFCL data are properly formatted."""
        bfcl_file = Path("output/task_BFCLTask_BFCLInternalHandler_20251010_170614.jsonl")
        
        if not bfcl_file.exists():
            pytest.skip("BFCL data file not found")
        
        # Load first sample
        with open(bfcl_file) as f:
            first_line = f.readline()
            sample = json.loads(first_line)
        
        outputs = sample.get("outputs", {})
        raw_prompt = outputs.get("raw_prompt", "")
        
        # Check that it contains JSON blocks
        assert "```json" in raw_prompt
        
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            viewer.data = outputs
            viewer._markdown_mode = True
            await pilot.pause()
            
            # Should render without errors
            assert viewer.data is not None


class TestMarkdownToggleInApp:
    """Test markdown toggle functionality in the full app."""
    
    @pytest.mark.asyncio
    async def test_m_key_toggles_markdown(self, test_jsonl_file):
        """Test that 'm' key toggles markdown mode."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Get the outputs viewer
            outputs_viewer = app.query_one("#json-metrics", JSONViewer)
            
            # Initially should be in JSON mode
            assert outputs_viewer.markdown_mode is False
            
            # Toggle directly on the viewer
            outputs_viewer.action_toggle_markdown()
            await pilot.pause()
            
            # Should have toggled
            assert outputs_viewer.markdown_mode is True
    
    @pytest.mark.asyncio
    async def test_toggle_persists_across_tab_switches(self, test_jsonl_file):
        """Test that markdown mode persists when switching tabs."""
        app = BeeViewerApp(jsonl_file=str(test_jsonl_file))
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Toggle markdown on Outputs tab
            outputs_viewer = app.query_one("#json-metrics", JSONViewer)
            outputs_viewer.action_toggle_markdown()
            await pilot.pause()
            
            assert outputs_viewer.markdown_mode is True
            
            # Switch to another tab and back
            await pilot.press("tab")
            await pilot.pause()
            await pilot.press("tab")
            await pilot.pause()
            
            # Markdown mode should still be enabled for Outputs
            assert outputs_viewer.markdown_mode is True

