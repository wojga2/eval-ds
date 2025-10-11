"""
Tests for nested markdown detection and JSON prettification in any text field.
"""

import pytest
import json
from bee_sample_viewer.widgets import JSONViewer


class TestNestedMarkdownDetection:
    """Test that markdown is detected in nested fields."""
    
    @pytest.mark.asyncio
    async def test_detects_markdown_in_nested_dict(self):
        """Test markdown detection in nested dictionary fields."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            test_data = {
                "metadata": {
                    "raw_prompt": "## System Preamble\nThis is a test with markdown headers. " * 3
                }
            }
            
            # Should detect markdown in nested field
            assert viewer._has_markdown_content(test_data) is True
    
    @pytest.mark.asyncio
    async def test_detects_markdown_in_deeply_nested_dict(self):
        """Test markdown detection in deeply nested structures."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            test_data = {
                "level1": {
                    "level2": {
                        "level3": {
                            "content": "## Deep Markdown\n```python\ncode\n```\n" * 3
                        }
                    }
                }
            }
            
            assert viewer._has_markdown_content(test_data) is True
    
    @pytest.mark.asyncio
    async def test_detects_markdown_in_list(self):
        """Test markdown detection in list items."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            test_data = {
                "items": [
                    "short text",
                    "## Markdown Header\nWith some content that's long enough. " * 3
                ]
            }
            
            assert viewer._has_markdown_content(test_data) is True
    
    @pytest.mark.asyncio
    async def test_no_false_positives_for_nested_plain_text(self):
        """Test that plain text in nested structures isn't detected as markdown."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            test_data = {
                "metadata": {
                    "description": "Just plain text without any markdown indicators."
                }
            }
            
            assert viewer._has_markdown_content(test_data) is False


class TestJSONDetection:
    """Test JSON detection and prettification in text fields."""
    
    @pytest.mark.asyncio
    async def test_detects_json_object_in_string(self):
        """Test that JSON objects in strings are detected."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            json_str = '{"name": "test", "value": 42, "nested": {"key": "value"}}'
            
            assert viewer._looks_like_json(json_str) is True
    
    @pytest.mark.asyncio
    async def test_detects_json_array_in_string(self):
        """Test that JSON arrays in strings are detected."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            json_str = '[1, 2, 3, {"key": "value"}]'
            
            assert viewer._looks_like_json(json_str) is True
    
    @pytest.mark.asyncio
    async def test_rejects_invalid_json(self):
        """Test that invalid JSON is not detected as JSON."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            # Invalid JSON strings
            invalid_jsons = [
                '{invalid json}',
                '{"unclosed": ',
                'not json at all',
                '{name: "test"}',  # Missing quotes
            ]
            
            for invalid in invalid_jsons:
                assert viewer._looks_like_json(invalid) is False
    
    @pytest.mark.asyncio
    async def test_prettifies_json_string(self):
        """Test that JSON strings are prettified."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            compact_json = '{"name":"test","nested":{"key":"value"},"array":[1,2,3]}'
            rendered = viewer._render_json_string(compact_json)
            
            # Should return a Syntax object (not crash)
            assert rendered is not None


class TestRenderValue:
    """Test the _render_value method for various data types."""
    
    @pytest.mark.asyncio
    async def test_renders_none(self):
        """Test rendering None values."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            rendered = viewer._render_value(None)
            assert rendered is not None
    
    @pytest.mark.asyncio
    async def test_renders_short_string(self):
        """Test rendering short strings."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            rendered = viewer._render_value("short text")
            assert rendered is not None
    
    @pytest.mark.asyncio
    async def test_renders_markdown_string(self):
        """Test rendering markdown strings."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            markdown_text = "## Header\n```python\ncode\n```\nMore text. " * 3
            rendered = viewer._render_value(markdown_text)
            assert rendered is not None
    
    @pytest.mark.asyncio
    async def test_renders_json_string(self):
        """Test rendering JSON strings."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            # Create a long JSON string (>100 chars)
            json_data = {"key": "value", "nested": {"a": 1, "b": 2}, "array": [1, 2, 3]}
            json_str = json.dumps(json_data)
            # Pad to make it long enough
            json_str = json_str + " " * (101 - len(json_str)) if len(json_str) < 101 else json_str
            
            rendered = viewer._render_value(json_str)
            assert rendered is not None
    
    @pytest.mark.asyncio
    async def test_renders_nested_dict(self):
        """Test rendering nested dictionaries."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            nested_dict = {
                "key1": "value1",
                "key2": {"nested": "value"}
            }
            rendered = viewer._render_value(nested_dict)
            assert rendered is not None
    
    @pytest.mark.asyncio
    async def test_renders_simple_list(self):
        """Test rendering simple lists."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            simple_list = [1, 2, 3, "string", True]
            rendered = viewer._render_value(simple_list)
            assert rendered is not None
    
    @pytest.mark.asyncio
    async def test_renders_complex_list(self):
        """Test rendering complex lists with nested structures."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            complex_list = [
                {"key": "value"},
                ["nested", "list"],
                "string"
            ]
            rendered = viewer._render_value(complex_list)
            assert rendered is not None


class TestIntegrationWithRealData:
    """Test with realistic data structures like TauBench."""
    
    @pytest.mark.asyncio
    async def test_taubench_style_nested_metadata(self):
        """Test with TauBench-style nested metadata structure."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            # Simulate TauBench data structure
            test_data = {
                "metadata": {
                    "raw_prompt": "## System Instructions\n\nYou are a helpful assistant.\n\n```json\n{\"key\": \"value\"}\n```\n" * 3,
                    "other_field": "plain text"
                },
                "result": "some result"
            }
            
            # Should detect markdown in nested field
            assert viewer._has_markdown_content(test_data) is True
            
            # Set data and toggle markdown
            viewer.data = test_data
            viewer._markdown_mode = True
            await pilot.pause()
            
            # Should not crash
            assert viewer.data is not None
    
    @pytest.mark.asyncio
    async def test_json_string_in_nested_field(self):
        """Test JSON string prettification in nested fields."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            # Long valid JSON string in nested field
            json_obj = {"key": "value", "nested": {"a": 1, "b": 2}, "long_array": list(range(20))}
            json_str = json.dumps(json_obj)
            test_data = {
                "config": {
                    "settings": json_str
                }
            }
            
            # Should detect as JSON and prettify
            assert viewer._looks_like_json(json_str) is True
            
            viewer.data = test_data
            viewer._markdown_mode = True
            await pilot.pause()
            
            # Should not crash
            assert viewer.data is not None
    
    @pytest.mark.asyncio
    async def test_mixed_content_rendering(self):
        """Test rendering mixed content (markdown, JSON, plain text)."""
        viewer = JSONViewer(id="test")
        
        from textual.app import App
        app = App()
        async with app.run_test() as pilot:
            await pilot.app.mount(viewer)
            await pilot.pause()
            
            test_data = {
                "markdown_field": "## Header\nSome **bold** text.\n" * 5,
                "json_field": '{"compact":"json","array":[1,2,3]}' + " " * 50,
                "plain_text": "Just regular text",
                "nested": {
                    "inner_markdown": "```python\nprint('hello')\n```\n" * 5
                }
            }
            
            assert viewer._has_markdown_content(test_data) is True
            
            viewer.data = test_data
            viewer._markdown_mode = True
            await pilot.pause()
            
            # Should not crash with mixed content
            assert viewer.data is not None

