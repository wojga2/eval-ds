"""
Tests for recursive nested JSON detection and formatting in token sections.

Tests that JSON strings within JSON objects (e.g., in TOOL_RESULT "output" fields)
are automatically detected, parsed, and formatted recursively.
"""

import pytest
import json
from bee_sample_viewer.widgets import JSONViewer


class TestNestedJSONExpansion:
    """Tests for the _expand_nested_json helper method."""
    
    def test_simple_string_passthrough(self):
        """Test that simple strings are passed through unchanged."""
        viewer = JSONViewer()
        result = viewer._expand_nested_json("Hello World")
        assert result == "Hello World"
    
    def test_number_passthrough(self):
        """Test that numbers are passed through unchanged."""
        viewer = JSONViewer()
        assert viewer._expand_nested_json(42) == 42
        assert viewer._expand_nested_json(3.14) == 3.14
    
    def test_boolean_passthrough(self):
        """Test that booleans are passed through unchanged."""
        viewer = JSONViewer()
        assert viewer._expand_nested_json(True) is True
        assert viewer._expand_nested_json(False) is False
    
    def test_none_passthrough(self):
        """Test that None is passed through unchanged."""
        viewer = JSONViewer()
        assert viewer._expand_nested_json(None) is None
    
    def test_simple_dict_no_nesting(self):
        """Test dict with no nested JSON strings."""
        viewer = JSONViewer()
        data = {"key": "value", "number": 42}
        result = viewer._expand_nested_json(data)
        assert result == data
    
    def test_simple_list_no_nesting(self):
        """Test list with no nested JSON strings."""
        viewer = JSONViewer()
        data = ["a", "b", "c", 123]
        result = viewer._expand_nested_json(data)
        assert result == data
    
    def test_detects_json_string_in_dict(self):
        """Test detection of JSON string within a dict value."""
        viewer = JSONViewer()
        json_string = '{"name": "John", "age": 30}'
        data = {"output": json_string}
        result = viewer._expand_nested_json(data)
        
        assert "output" in result
        assert isinstance(result["output"], dict)
        assert "_nested_json_" in result["output"]
        assert result["output"]["_nested_json_"] is True
        assert "_content_" in result["output"]
        assert result["output"]["_content_"]["name"] == "John"
        assert result["output"]["_content_"]["age"] == 30
    
    def test_detects_json_array_string(self):
        """Test detection of JSON array string."""
        viewer = JSONViewer()
        json_string = '["a", "b", "c"]'
        data = {"items": json_string}
        result = viewer._expand_nested_json(data)
        
        assert "_nested_json_" in result["items"]
        assert result["items"]["_content_"] == ["a", "b", "c"]
    
    def test_deeply_nested_json_strings(self):
        """Test multiple levels of nested JSON strings."""
        viewer = JSONViewer()
        # Level 3: innermost JSON
        level3 = '{"level": 3, "data": "deep"}'
        # Level 2: contains level 3 as string
        level2 = json.dumps({"level": 2, "nested": level3})
        # Level 1: contains level 2 as string
        data = {"level": 1, "nested": level2}
        
        result = viewer._expand_nested_json(data)
        
        assert result["level"] == 1
        assert "_nested_json_" in result["nested"]
        assert result["nested"]["_content_"]["level"] == 2
        assert "_nested_json_" in result["nested"]["_content_"]["nested"]
        assert result["nested"]["_content_"]["nested"]["_content_"]["level"] == 3
    
    def test_invalid_json_string_left_unchanged(self):
        """Test that invalid JSON strings are left as-is."""
        viewer = JSONViewer()
        data = {"output": "{not valid json}"}
        result = viewer._expand_nested_json(data)
        
        assert result["output"] == "{not valid json}"
    
    def test_mixed_valid_and_invalid_json_strings(self):
        """Test mix of valid and invalid JSON strings."""
        viewer = JSONViewer()
        data = {
            "valid": '{"key": "value"}',
            "invalid": "{not json}",
            "plain": "just text"
        }
        result = viewer._expand_nested_json(data)
        
        assert "_nested_json_" in result["valid"]
        assert result["invalid"] == "{not json}"
        assert result["plain"] == "just text"


class TestNestedJSONInToolResults:
    """Tests for nested JSON in TOOL_RESULT sections (the main use case)."""
    
    def test_tool_result_with_nested_json_output(self):
        """Test typical TOOL_RESULT with JSON string in output field."""
        viewer = JSONViewer()
        
        # Simulate a tool result where output is a JSON string
        user_data = {"user_id": "123", "name": "John Doe", "email": "john@example.com"}
        tool_result = [{
            "tool_call_id": "1",
            "results": {
                "0": {
                    "output": json.dumps(user_data)
                }
            },
            "is_error": None
        }]
        
        result = viewer._expand_nested_json(tool_result)
        
        assert len(result) == 1
        output_value = result[0]["results"]["0"]["output"]
        assert "_nested_json_" in output_value
        assert output_value["_content_"]["user_id"] == "123"
        assert output_value["_content_"]["name"] == "John Doe"
    
    def test_tool_result_with_complex_nested_json(self):
        """Test TOOL_RESULT with complex nested JSON."""
        viewer = JSONViewer()
        
        # Complex user data with nested structures
        user_data = {
            "name": {"first": "John", "last": "Doe"},
            "address": {
                "street": "123 Main St",
                "city": "Springfield",
                "zip": "12345"
            },
            "orders": ["#W001", "#W002", "#W003"]
        }
        
        tool_result = [{
            "tool_call_id": "5",
            "results": {
                "0": {"output": json.dumps(user_data)}
            },
            "is_error": None
        }]
        
        result = viewer._expand_nested_json(tool_result)
        output = result[0]["results"]["0"]["output"]["_content_"]
        
        assert output["name"]["first"] == "John"
        assert output["address"]["city"] == "Springfield"
        assert len(output["orders"]) == 3
    
    def test_tool_result_with_doubly_nested_json(self):
        """Test TOOL_RESULT where output contains JSON that itself contains JSON."""
        viewer = JSONViewer()
        
        # Inner JSON (level 3)
        inner_json = {"product_id": "456", "price": 29.99}
        # Middle JSON (level 2) - contains inner as string
        middle_json = {
            "order_id": "#123",
            "item_details": json.dumps(inner_json)
        }
        # Outer structure (level 1) - contains middle as string
        tool_result = [{
            "tool_call_id": "10",
            "results": {
                "0": {"output": json.dumps(middle_json)}
            },
            "is_error": None
        }]
        
        result = viewer._expand_nested_json(tool_result)
        
        # Navigate through the nesting
        output = result[0]["results"]["0"]["output"]
        assert "_nested_json_" in output
        
        middle = output["_content_"]
        assert middle["order_id"] == "#123"
        assert "_nested_json_" in middle["item_details"]
        
        inner = middle["item_details"]["_content_"]
        assert inner["product_id"] == "456"
        assert inner["price"] == 29.99
    
    def test_tool_result_with_list_of_json_strings(self):
        """Test TOOL_RESULT where output is a list containing JSON strings."""
        viewer = JSONViewer()
        
        items = [
            '{"id": "1", "name": "Item A"}',
            '{"id": "2", "name": "Item B"}'
        ]
        
        tool_result = [{
            "tool_call_id": "7",
            "results": {
                "0": {"output": json.dumps(items)}
            },
            "is_error": None
        }]
        
        result = viewer._expand_nested_json(tool_result)
        output_list = result[0]["results"]["0"]["output"]["_content_"]
        
        assert len(output_list) == 2
        assert "_nested_json_" in output_list[0]
        assert output_list[0]["_content_"]["id"] == "1"
        assert output_list[1]["_content_"]["name"] == "Item B"
    
    def test_multiple_results_with_nested_json(self):
        """Test multiple tool results, some with nested JSON."""
        viewer = JSONViewer()
        
        tool_result = [
            {
                "tool_call_id": "1",
                "results": {"0": {"output": '{"status": "success"}'}},
                "is_error": None
            },
            {
                "tool_call_id": "2",
                "results": {"0": {"output": "plain text"}},
                "is_error": None
            },
            {
                "tool_call_id": "3",
                "results": {"0": {"output": '["a", "b", "c"]'}},
                "is_error": None
            }
        ]
        
        result = viewer._expand_nested_json(tool_result)
        
        # First result: JSON object
        assert "_nested_json_" in result[0]["results"]["0"]["output"]
        
        # Second result: plain text
        assert result[1]["results"]["0"]["output"] == "plain text"
        
        # Third result: JSON array
        assert "_nested_json_" in result[2]["results"]["0"]["output"]
        assert result[2]["results"]["0"]["output"]["_content_"] == ["a", "b", "c"]


class TestNestedJSONRenderingIntegration:
    """Integration tests for nested JSON rendering."""
    
    def test_full_rendering_with_nested_json(self):
        """Test complete rendering pipeline with nested JSON."""
        viewer = JSONViewer()
        
        # Create a TOOL_RESULT with nested JSON
        user_data = '{"name": "Alice", "id": "u123"}'
        tool_result_json = json.dumps([{
            "tool_call_id": "0",
            "results": {"0": {"output": user_data}},
            "is_error": None
        }])
        
        # Try to render as JSON
        rendered = viewer._try_render_as_json(tool_result_json)
        
        assert rendered is not None
    
    def test_taubench_style_result(self):
        """Test with actual TauBench-style TOOL_RESULT."""
        viewer = JSONViewer()
        
        # Simulating actual TauBench data
        output_data = {
            "name": {"first_name": "Yusuf", "last_name": "Rossi"},
            "address": {
                "address1": "763 Broadway",
                "address2": "Suite 135",
                "city": "Philadelphia",
                "state": "PA",
                "zip": "19122"
            },
            "email": "yusuf.rossi@example.com",
            "payment_methods": {
                "credit_card_001": {
                    "brand": "mastercard",
                    "last_four": "2478"
                }
            },
            "orders": ["#W001", "#W002"]
        }
        
        tool_result = [{
            "tool_call_id": "1",
            "results": {
                "0": {"output": json.dumps(output_data)}
            },
            "is_error": None
        }]
        
        result = viewer._expand_nested_json(tool_result)
        
        # Verify nested JSON was expanded
        output = result[0]["results"]["0"]["output"]
        assert "_nested_json_" in output
        assert output["_content_"]["name"]["first_name"] == "Yusuf"
        assert output["_content_"]["address"]["city"] == "Philadelphia"
        assert len(output["_content_"]["orders"]) == 2


class TestEdgeCases:
    """Edge cases for nested JSON handling."""
    
    def test_empty_json_string(self):
        """Test empty JSON object string."""
        viewer = JSONViewer()
        data = {"output": "{}"}
        result = viewer._expand_nested_json(data)
        
        assert "_nested_json_" in result["output"]
        assert result["output"]["_content_"] == {}
    
    def test_json_string_with_whitespace(self):
        """Test JSON string with surrounding whitespace."""
        viewer = JSONViewer()
        data = {"output": '  {"key": "value"}  '}
        result = viewer._expand_nested_json(data)
        
        assert "_nested_json_" in result["output"]
        assert result["output"]["_content_"]["key"] == "value"
    
    def test_json_string_with_special_characters(self):
        """Test JSON string with special characters."""
        viewer = JSONViewer()
        special_data = {"text": "Hello\nWorld\t!", "price": "$99.99"}
        data = {"output": json.dumps(special_data)}
        result = viewer._expand_nested_json(data)
        
        assert "_nested_json_" in result["output"]
        assert "Hello\nWorld\t!" in result["output"]["_content_"]["text"]
    
    def test_json_string_with_unicode(self):
        """Test JSON string with unicode characters."""
        viewer = JSONViewer()
        unicode_data = {"emoji": "🎉", "chinese": "你好"}
        data = {"output": json.dumps(unicode_data)}
        result = viewer._expand_nested_json(data)
        
        assert "_nested_json_" in result["output"]
        assert result["output"]["_content_"]["emoji"] == "🎉"
    
    def test_very_short_json_like_string(self):
        """Test that very short strings like '{}' or '[]' are handled."""
        viewer = JSONViewer()
        
        # These should be expanded
        data1 = {"output": "{}"}
        result1 = viewer._expand_nested_json(data1)
        assert "_nested_json_" in result1["output"]
        
        data2 = {"output": "[]"}
        result2 = viewer._expand_nested_json(data2)
        assert "_nested_json_" in result2["output"]
    
    def test_string_starting_with_brace_but_not_json(self):
        """Test string that starts with { but is not valid JSON."""
        viewer = JSONViewer()
        data = {"output": "{this is not json at all}"}
        result = viewer._expand_nested_json(data)
        
        # Should be left as-is
        assert result["output"] == "{this is not json at all}"
    
    def test_null_value_in_nested_json(self):
        """Test null/None values in nested JSON."""
        viewer = JSONViewer()
        nested_data = {"key": None, "other": "value"}
        data = {"output": json.dumps(nested_data)}
        result = viewer._expand_nested_json(data)
        
        assert "_nested_json_" in result["output"]
        assert result["output"]["_content_"]["key"] is None
        assert result["output"]["_content_"]["other"] == "value"

