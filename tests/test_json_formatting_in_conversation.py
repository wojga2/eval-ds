"""Test JSON formatting in conversation viewer."""
import pytest
from bee_sample_viewer.conversation_viewer import ConversationViewer
from rich.console import Console


class TestJSONExpansion:
    """Test nested JSON expansion."""
    
    def test_expands_simple_json_string(self):
        """Test that simple JSON strings are expanded."""
        viewer = ConversationViewer()
        
        json_str = '{"key": "value", "number": 42}'
        result = viewer._expand_nested_json(json_str)
        
        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["number"] == 42
    
    def test_expands_nested_json_string(self):
        """Test that nested JSON strings are expanded recursively."""
        viewer = ConversationViewer()
        
        # A JSON string containing another JSON string (escaped)
        inner_json = '{"inner": "data"}'
        escaped_inner = inner_json.replace('"', '\\"')
        outer_json = '{"outer": "value", "nested": "' + escaped_inner + '"}'
        
        result = viewer._expand_nested_json(outer_json)
        
        assert isinstance(result, dict)
        assert result["outer"] == "value"
        # The nested JSON should also be expanded
        assert isinstance(result["nested"], dict)
        assert result["nested"]["inner"] == "data"
    
    def test_expands_json_in_dict(self):
        """Test that JSON strings within dicts are expanded."""
        viewer = ConversationViewer()
        
        data = {
            "field1": "normal",
            "field2": '{"json": "value"}'
        }
        
        result = viewer._expand_nested_json(data)
        
        assert result["field1"] == "normal"
        assert isinstance(result["field2"], dict)
        assert result["field2"]["json"] == "value"
    
    def test_expands_json_in_list(self):
        """Test that JSON strings within lists are expanded."""
        viewer = ConversationViewer()
        
        data = [
            "normal string",
            '{"json": "value"}',
            '["nested", "array"]'
        ]
        
        result = viewer._expand_nested_json(data)
        
        assert result[0] == "normal string"
        assert isinstance(result[1], dict)
        assert result[1]["json"] == "value"
        assert isinstance(result[2], list)
        assert result[2] == ["nested", "array"]
    
    def test_handles_max_depth_limit(self):
        """Test that expansion has a max_depth parameter (prevents infinite loops)."""
        viewer = ConversationViewer()
        
        # Test that the method accepts max_depth parameter
        # and doesn't crash with deeply nested structures
        data = {"level": 1, "nested": '{"level": 2}'}
        result = viewer._expand_nested_json(data, max_depth=1)
        
        # Should handle it without crashing
        assert result is not None


class TestToolCallFormatting:
    """Test tool call parameter formatting."""
    
    def test_formats_simple_parameters(self):
        """Test that simple tool call parameters are formatted."""
        viewer = ConversationViewer()
        
        params = {"arg1": "value1", "arg2": 42}
        syntax = viewer._format_json_with_syntax(params)
        
        # Check that it's a Syntax object
        assert syntax is not None
        assert hasattr(syntax, 'code')
        
        # Check the formatted JSON contains proper indentation
        assert '"arg1"' in syntax.code
        assert '"value1"' in syntax.code
    
    def test_formats_nested_json_in_parameters(self):
        """Test that nested JSON strings in parameters are expanded."""
        viewer = ConversationViewer()
        
        params = {
            "query": '{"field": "value"}',
            "limit": 10
        }
        
        syntax = viewer._format_json_with_syntax(params)
        
        # The nested JSON should be expanded and formatted
        assert '"query"' in syntax.code
        assert '"field"' in syntax.code
        assert '"value"' in syntax.code


class TestToolResultFormatting:
    """Test tool result formatting."""
    
    def test_formats_json_in_tool_result_text(self):
        """Test that JSON in tool result text field is formatted."""
        viewer = ConversationViewer()
        
        turn = {
            "role": "Tool",
            "tool_results": [
                {
                    "tool_call_id": "call_123",
                    "outputs": [
                        {
                            "text": '{"result": "success", "count": 5}',
                            "type": "json"
                        }
                    ]
                }
            ]
        }
        
        panel = viewer._render_tool_turn(turn, 0)
        
        # Render to check content
        console = Console(width=80)
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        
        # Should contain formatted JSON
        assert "result" in output
        assert "success" in output
        assert "count" in output
    
    def test_formats_nested_json_in_tool_results(self):
        """Test that deeply nested JSON in tool results is formatted."""
        viewer = ConversationViewer()
        
        # Tool result with nested JSON strings
        inner_json = '{"inner": "data"}'
        escaped_inner = inner_json.replace('"', '\\"')
        outer_json = '{"status": "ok", "data": "' + escaped_inner + '"}'
        
        turn = {
            "role": "Tool",
            "tool_results": [
                {
                    "tool_call_id": "call_456",
                    "outputs": [
                        {
                            "text": outer_json,
                            "type": "json"
                        }
                    ]
                }
            ]
        }
        
        panel = viewer._render_tool_turn(turn, 0)
        
        # Render to check content
        console = Console(width=80)
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        
        # Should contain both outer and inner JSON expanded
        assert "status" in output
        assert "data" in output
        assert "inner" in output
    
    def test_handles_non_json_tool_results(self):
        """Test that non-JSON tool results are handled gracefully."""
        viewer = ConversationViewer()
        
        turn = {
            "role": "Tool",
            "tool_results": [
                {
                    "tool_call_id": "call_789",
                    "outputs": [
                        {
                            "text": "Just a plain text result",
                            "type": "text"
                        }
                    ]
                }
            ]
        }
        
        panel = viewer._render_tool_turn(turn, 0)
        
        # Should not crash
        assert panel is not None
        
        # Render to check content
        console = Console(width=80)
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        
        assert "Just a plain text result" in output


class TestFullConversationWithJSON:
    """Test full conversation rendering with JSON formatting."""
    
    @pytest.mark.asyncio
    async def test_full_conversation_with_tool_calls_and_results(self):
        """Test a complete conversation with tool calls and JSON results."""
        from textual.app import App
        
        viewer = ConversationViewer()
        
        conversation = [
            {
                "role": "User",
                "content": [{"text": "Search for users", "content_type": "text"}],
                "rationale": None,
                "tool_calls": None,
                "tool_results": None,
            },
            {
                "role": "Chatbot",
                "content": None,
                "rationale": "I'll search the database",
                "tool_calls": [
                    {
                        "name": "database_query",
                        "parameters": {"query": '{"field": "name"}', "limit": 5},
                        "tool_call_id": "call_123"
                    }
                ],
                "tool_results": None,
            },
            {
                "role": "Tool",
                "content": None,
                "rationale": None,
                "tool_calls": None,
                "tool_results": [
                    {
                        "tool_call_id": "call_123",
                        "outputs": [
                            {
                                "text": '{"results": [{"id": 1, "name": "Alice"}], "count": 1}',
                                "type": "json"
                            }
                        ]
                    }
                ]
            }
        ]
        
        class TestApp(App):
            def compose(self):
                yield viewer
        
        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            viewer.conversation = conversation
            await pilot.pause()
            
            # Check that all turns were rendered
            assert len(viewer.conversation) == 3
            
            # Manually render to check content
            renderables = []
            for i, turn in enumerate(viewer.conversation):
                r = viewer._render_turn(turn, i)
                if r:
                    renderables.append(r)
            
            assert len(renderables) == 3
            
            # Render to string to verify JSON formatting
            from rich.console import Group, Console
            group = Group(*renderables)
            console = Console(width=120)
            with console.capture() as capture:
                console.print(group)
            output = capture.get()
            
            # Should contain properly formatted JSON
            assert "query" in output
            assert "field" in output
            assert "name" in output
            assert "results" in output
            assert "Alice" in output

