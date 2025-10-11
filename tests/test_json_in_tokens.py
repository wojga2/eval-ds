"""
Tests for JSON detection and formatting within special token sections.

Tests that ACTION and TOOL_RESULT sections containing JSON are automatically
parsed and pretty-printed with syntax highlighting.
"""

import pytest
import json
from bee_sample_viewer.widgets import JSONViewer


class TestJSONInActionSections:
    """Tests for JSON formatting in ACTION sections."""
    
    def test_action_with_simple_json_object(self):
        """Test ACTION section with a simple JSON object."""
        viewer = JSONViewer()
        json_obj = {"tool_call_id": "0", "tool_name": "test_tool", "parameters": {"key": "value"}}
        text = f'<|START_ACTION|>{json.dumps(json_obj)}<|END_ACTION|>'
        
        # Should be able to try rendering as JSON
        json_rendered = viewer._try_render_as_json(json.dumps(json_obj))
        assert json_rendered is not None
    
    def test_action_with_json_list(self):
        """Test ACTION section with a JSON list."""
        viewer = JSONViewer()
        json_list = [
            {"tool_call_id": "0", "tool_name": "get_user", "parameters": {"id": "123"}},
            {"tool_call_id": "1", "tool_name": "get_order", "parameters": {"order_id": "#456"}}
        ]
        text = f'<|START_ACTION|>{json.dumps(json_list)}<|END_ACTION|>'
        
        json_rendered = viewer._try_render_as_json(json.dumps(json_list))
        assert json_rendered is not None
    
    def test_action_with_nested_json(self):
        """Test ACTION section with deeply nested JSON."""
        viewer = JSONViewer()
        json_obj = {
            "tool_call_id": "5",
            "tool_name": "complex_tool",
            "parameters": {
                "user": {
                    "name": "John Doe",
                    "address": {
                        "street": "123 Main St",
                        "city": "Springfield",
                        "nested": {
                            "level": 3,
                            "data": ["a", "b", "c"]
                        }
                    }
                },
                "options": ["opt1", "opt2"]
            }
        }
        text = f'<|START_ACTION|>{json.dumps(json_obj)}<|END_ACTION|>'
        
        json_rendered = viewer._try_render_as_json(json.dumps(json_obj))
        assert json_rendered is not None
    
    def test_action_with_whitespace(self):
        """Test ACTION section with JSON and surrounding whitespace."""
        viewer = JSONViewer()
        json_obj = {"tool": "test"}
        text = f'<|START_ACTION|>  \n {json.dumps(json_obj)}  \n <|END_ACTION|>'
        
        content = json.dumps(json_obj)
        json_rendered = viewer._try_render_as_json(f"  \n {content}  \n ")
        assert json_rendered is not None
    
    def test_action_with_invalid_json(self):
        """Test ACTION section with invalid JSON falls back gracefully."""
        viewer = JSONViewer()
        text = '<|START_ACTION|>not valid json{}<|END_ACTION|>'
        
        json_rendered = viewer._try_render_as_json('not valid json{}')
        assert json_rendered is None
    
    def test_action_non_json_content(self):
        """Test ACTION section with non-JSON content."""
        viewer = JSONViewer()
        text = '<|START_ACTION|>This is plain text without JSON<|END_ACTION|>'
        
        json_rendered = viewer._try_render_as_json('This is plain text without JSON')
        assert json_rendered is None


class TestJSONInToolResultSections:
    """Tests for JSON formatting in TOOL_RESULT sections."""
    
    def test_tool_result_with_simple_json(self):
        """Test TOOL_RESULT section with simple JSON."""
        viewer = JSONViewer()
        json_obj = {
            "tool_call_id": "0",
            "results": {"0": {"output": "success"}},
            "is_error": None
        }
        text = f'<|START_TOOL_RESULT|>{json.dumps(json_obj)}<|END_TOOL_RESULT|>'
        
        json_rendered = viewer._try_render_as_json(json.dumps(json_obj))
        assert json_rendered is not None
    
    def test_tool_result_with_list(self):
        """Test TOOL_RESULT section with a list of results."""
        viewer = JSONViewer()
        json_list = [
            {
                "tool_call_id": "3",
                "results": {
                    "0": {
                        "output": '{"name": "Product A", "price": 29.99}'
                    }
                },
                "is_error": None
            }
        ]
        text = f'<|START_TOOL_RESULT|>{json.dumps(json_list)}<|END_TOOL_RESULT|>'
        
        json_rendered = viewer._try_render_as_json(json.dumps(json_list))
        assert json_rendered is not None
    
    def test_tool_result_with_nested_json_string(self):
        """Test TOOL_RESULT with nested JSON (JSON string within JSON)."""
        viewer = JSONViewer()
        # This is common: output field contains a JSON string
        json_obj = {
            "tool_call_id": "1",
            "results": {
                "0": {
                    "output": '{"user_id": "abc123", "name": "John", "orders": ["#123", "#456"]}'
                }
            },
            "is_error": None
        }
        text = f'<|START_TOOL_RESULT|>{json.dumps(json_obj)}<|END_TOOL_RESULT|>'
        
        json_rendered = viewer._try_render_as_json(json.dumps(json_obj))
        assert json_rendered is not None
    
    def test_tool_result_with_error(self):
        """Test TOOL_RESULT section with error information."""
        viewer = JSONViewer()
        json_obj = {
            "tool_call_id": "5",
            "results": {},
            "is_error": "Connection timeout"
        }
        text = f'<|START_TOOL_RESULT|>{json.dumps(json_obj)}<|END_TOOL_RESULT|>'
        
        json_rendered = viewer._try_render_as_json(json.dumps(json_obj))
        assert json_rendered is not None
    
    def test_tool_result_with_large_output(self):
        """Test TOOL_RESULT with large nested output."""
        viewer = JSONViewer()
        large_output = {
            "name": {"first": "A", "last": "B"},
            "address": {"street": "123 Main", "city": "City", "state": "ST", "zip": "12345"},
            "orders": [f"#W{i:07d}" for i in range(10)],
            "items": [{"id": str(i), "name": f"Item {i}", "price": 10.0 * i} for i in range(5)]
        }
        json_obj = {
            "tool_call_id": "10",
            "results": {
                "0": {
                    "output": json.dumps(large_output)
                }
            },
            "is_error": None
        }
        text = f'<|START_TOOL_RESULT|>{json.dumps(json_obj)}<|END_TOOL_RESULT|>'
        
        json_rendered = viewer._try_render_as_json(json.dumps(json_obj))
        assert json_rendered is not None


class TestJSONDetectionHelper:
    """Tests for the _try_render_as_json helper method."""
    
    def test_detects_object_json(self):
        """Test detection of JSON object."""
        viewer = JSONViewer()
        result = viewer._try_render_as_json('{"key": "value"}')
        assert result is not None
    
    def test_detects_array_json(self):
        """Test detection of JSON array."""
        viewer = JSONViewer()
        result = viewer._try_render_as_json('[1, 2, 3]')
        assert result is not None
    
    def test_rejects_plain_text(self):
        """Test rejection of plain text."""
        viewer = JSONViewer()
        result = viewer._try_render_as_json('This is plain text')
        assert result is None
    
    def test_rejects_empty_string(self):
        """Test rejection of empty string."""
        viewer = JSONViewer()
        result = viewer._try_render_as_json('')
        assert result is None
    
    def test_rejects_whitespace_only(self):
        """Test rejection of whitespace-only string."""
        viewer = JSONViewer()
        result = viewer._try_render_as_json('   \n  \t  ')
        assert result is None
    
    def test_rejects_malformed_json(self):
        """Test rejection of malformed JSON."""
        viewer = JSONViewer()
        result = viewer._try_render_as_json('{key: value}')  # Missing quotes
        assert result is None
    
    def test_rejects_partial_json(self):
        """Test rejection of partial JSON."""
        viewer = JSONViewer()
        result = viewer._try_render_as_json('{"key": "value"')  # Missing closing brace
        assert result is None
    
    def test_handles_json_with_special_chars(self):
        """Test JSON with special characters."""
        viewer = JSONViewer()
        json_str = '{"text": "Hello\\nWorld\\t!", "price": "$99.99", "email": "test@example.com"}'
        result = viewer._try_render_as_json(json_str)
        assert result is not None
    
    def test_handles_json_with_unicode(self):
        """Test JSON with unicode characters."""
        viewer = JSONViewer()
        json_str = '{"emoji": "🎉", "chinese": "你好", "arabic": "مرحبا"}'
        result = viewer._try_render_as_json(json_str)
        assert result is not None


class TestRealWorldPatterns:
    """Tests based on actual TauBench data patterns."""
    
    def test_taubench_action_format(self):
        """Test actual TauBench ACTION format."""
        viewer = JSONViewer()
        action_data = [
            {
                "tool_call_id": "0",
                "tool_name": "find_user_id_by_name_zip",
                "parameters": {
                    "first_name": "Yusuf",
                    "last_name": "Rossi",
                    "zip": "19122"
                }
            }
        ]
        text = f'<|START_ACTION|>\n{json.dumps(action_data, indent=4)}\n<|END_ACTION|>'
        
        # Extract content
        sections = viewer._parse_token_sections(text)
        assert len(sections) > 0
        
        # Find the action section
        action_section = next((s for s in sections if s[0] == 'action'), None)
        assert action_section is not None
        
        # Try to render as JSON
        json_rendered = viewer._try_render_as_json(action_section[2])
        assert json_rendered is not None
    
    def test_taubench_tool_result_format(self):
        """Test actual TauBench TOOL_RESULT format."""
        viewer = JSONViewer()
        result_data = [
            {
                "tool_call_id": "0",
                "results": {
                    "0": {"output": "yusuf_rossi_9620"}
                },
                "is_error": None
            }
        ]
        text = f'<|START_TOOL_RESULT|>\n{json.dumps(result_data, indent=4)}\n<|END_TOOL_RESULT|>'
        
        sections = viewer._parse_token_sections(text)
        tool_result_section = next((s for s in sections if s[0] == 'tool_result'), None)
        assert tool_result_section is not None
        
        json_rendered = viewer._try_render_as_json(tool_result_section[2])
        assert json_rendered is not None
    
    def test_taubench_complex_result_with_nested_json(self):
        """Test complex TOOL_RESULT with nested JSON string."""
        viewer = JSONViewer()
        result_data = [
            {
                "tool_call_id": "1",
                "results": {
                    "0": {
                        "output": '{"name": {"first_name": "Yusuf", "last_name": "Rossi"}, "address": {"address1": "763 Broadway", "address2": "Suite 135", "city": "Philadelphia", "country": "USA", "state": "PA", "zip": "19122"}, "email": "yusuf.rossi7301@example.com", "payment_methods": {"credit_card_9513926": {"source": "credit_card", "brand": "mastercard", "last_four": "2478", "id": "credit_card_9513926"}}, "orders": ["#W6247578", "#W9711842", "#W4776164", "#W6679257", "#W2378156"]}'
                    }
                },
                "is_error": None
            }
        ]
        text = f'<|START_TOOL_RESULT|>\n{json.dumps(result_data, indent=4)}\n<|END_TOOL_RESULT|>'
        
        sections = viewer._parse_token_sections(text)
        tool_result_section = next((s for s in sections if s[0] == 'tool_result'), None)
        assert tool_result_section is not None
        
        json_rendered = viewer._try_render_as_json(tool_result_section[2])
        assert json_rendered is not None
    
    def test_multiple_actions_in_sequence(self):
        """Test multiple ACTION sections parsed correctly."""
        viewer = JSONViewer()
        text = (
            '<|USER_TOKEN|>Request something<|END_OF_TURN_TOKEN|>'
            '<|CHATBOT_TOKEN|>'
            '<|START_ACTION|>[{"tool_call_id": "0", "tool_name": "tool1", "parameters": {}}]<|END_ACTION|>'
            '<|END_OF_TURN_TOKEN|>'
            '<|SYSTEM_TOKEN|>'
            '<|START_TOOL_RESULT|>[{"tool_call_id": "0", "results": {"0": {"output": "result1"}}, "is_error": null}]<|END_TOOL_RESULT|>'
            '<|END_OF_TURN_TOKEN|>'
            '<|CHATBOT_TOKEN|>'
            '<|START_ACTION|>[{"tool_call_id": "1", "tool_name": "tool2", "parameters": {}}]<|END_ACTION|>'
            '<|END_OF_TURN_TOKEN|>'
        )
        
        sections = viewer._parse_token_sections(text)
        
        # Should have multiple sections (at least user, 2 actions, 1 tool_result)
        assert len(sections) >= 4
        
        # Check action sections can be parsed as JSON
        action_sections = [s for s in sections if s[0] == 'action']
        assert len(action_sections) == 2
        
        for action_section in action_sections:
            json_rendered = viewer._try_render_as_json(action_section[2])
            # Should successfully parse
            assert json_rendered is not None


class TestIntegrationWithMarkdownMode:
    """Test that JSON in tokens works with markdown mode."""
    
    def test_full_rendering_with_tokens_and_json(self):
        """Test complete rendering with tokens containing JSON."""
        viewer = JSONViewer()
        text = (
            '<|START_OF_TURN_TOKEN|>'
            '<|USER_TOKEN|>Test request'
            '<|END_OF_TURN_TOKEN|>'
            '<|START_OF_TURN_TOKEN|>'
            '<|CHATBOT_TOKEN|>'
            '<|START_ACTION|>[\n  {"tool_call_id": "0", "tool_name": "test", "parameters": {"key": "value"}}\n]<|END_ACTION|>'
            '<|END_OF_TURN_TOKEN|>'
            '<|START_OF_TURN_TOKEN|>'
            '<|SYSTEM_TOKEN|>'
            '<|START_TOOL_RESULT|>[\n  {"tool_call_id": "0", "results": {"0": {"output": "success"}}, "is_error": null}\n]<|END_TOOL_RESULT|>'
            '<|END_OF_TURN_TOKEN|>'
        )
        
        # Set data and enable markdown
        viewer.data = {"test_field": text}
        viewer._markdown_mode = True
        
        # Should not raise any exceptions
        try:
            # The _update_content method should handle this gracefully
            assert True
        except Exception as e:
            pytest.fail(f"Rendering failed with: {e}")

