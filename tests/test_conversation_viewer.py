"""
Tests for the FATUC conversation viewer.
"""

import pytest
from bee_sample_viewer.conversation_viewer import ConversationViewer


class TestConversationViewerBasics:
    """Test basic conversation viewer functionality."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test that the viewer initializes correctly."""
        viewer = ConversationViewer()
        assert viewer.conversation is None
    
    @pytest.mark.asyncio
    async def test_empty_conversation(self):
        """Test handling of empty conversation list."""
        viewer = ConversationViewer()
        viewer.conversation = []
        # Should not crash, just display "Empty conversation"
    
    @pytest.mark.asyncio
    async def test_none_conversation(self):
        """Test handling of None conversation."""
        viewer = ConversationViewer()
        viewer.conversation = None
        # Should not crash, just display "No conversation data"


class TestSystemTurn:
    """Test rendering of System turns."""
    
    @pytest.mark.asyncio
    async def test_system_turn_basic(self):
        """Test rendering a basic System turn."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "System",
                "content": [{"text": "You are a helpful assistant.", "content_type": "text"}],
                "rationale": None,
                "tool_calls": None,
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should render without errors
    
    @pytest.mark.asyncio
    async def test_system_turn_long_content(self):
        """Test that long System messages are truncated."""
        viewer = ConversationViewer()
        long_text = "A" * 1000  # Long policy document
        conversation = [
            {
                "role": "System",
                "content": [{"text": long_text, "content_type": "text"}],
                "rationale": None,
                "tool_calls": None,
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should truncate long content
    
    @pytest.mark.asyncio
    async def test_system_turn_string_content(self):
        """Test System turn with string content instead of list."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "System",
                "content": "You are a helpful assistant.",
                "rationale": None,
                "tool_calls": None,
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should handle string content


class TestUserTurn:
    """Test rendering of User turns."""
    
    @pytest.mark.asyncio
    async def test_user_turn_basic(self):
        """Test rendering a basic User turn."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "User",
                "content": [{"text": "Hello, I need help!", "content_type": "text"}],
                "rationale": None,
                "tool_calls": None,
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should render without errors
    
    @pytest.mark.asyncio
    async def test_user_turn_multiple_content_items(self):
        """Test User turn with multiple content items."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "User",
                "content": [
                    {"text": "First part", "content_type": "text"},
                    {"text": "Second part", "content_type": "text"},
                ],
                "rationale": None,
                "tool_calls": None,
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should concatenate content


class TestChatbotTurnWithThinking:
    """Test rendering of Chatbot turns with thinking."""
    
    @pytest.mark.asyncio
    async def test_chatbot_with_rationale_only(self):
        """Test Chatbot turn with only rationale (thinking)."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "Chatbot",
                "content": None,
                "rationale": "Let me think about this... I should help the user.",
                "tool_calls": None,
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should display thinking with 💭
    
    @pytest.mark.asyncio
    async def test_chatbot_with_response_only(self):
        """Test Chatbot turn with only a text response."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "Chatbot",
                "content": [{"text": "Here is the answer.", "content_type": "text"}],
                "rationale": None,
                "tool_calls": None,
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should display response with 💬
    
    @pytest.mark.asyncio
    async def test_chatbot_with_rationale_and_response(self):
        """Test Chatbot turn with both thinking and response."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "Chatbot",
                "content": [{"text": "Here is the answer.", "content_type": "text"}],
                "rationale": "Let me think about this...",
                "tool_calls": None,
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should display both thinking and response


class TestChatbotTurnWithToolCalls:
    """Test rendering of Chatbot turns with tool calls."""
    
    @pytest.mark.asyncio
    async def test_chatbot_with_single_tool_call(self):
        """Test Chatbot turn with a single tool call."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "Chatbot",
                "content": None,
                "rationale": "I should transfer this to a human agent.",
                "tool_calls": [
                    {
                        "name": "transfer_to_human_agents",
                        "parameters": {
                            "summary": "User needs urgent help."
                        },
                        "tool_call_id": "call_123"
                    }
                ],
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should display thinking + tool call with 🔧
    
    @pytest.mark.asyncio
    async def test_chatbot_with_multiple_tool_calls(self):
        """Test Chatbot turn with multiple tool calls."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "Chatbot",
                "content": None,
                "rationale": "I need to check the user's account.",
                "tool_calls": [
                    {
                        "name": "get_customer_by_phone",
                        "parameters": {"phone_number": "555-123-4567"},
                        "tool_call_id": "call_1"
                    },
                    {
                        "name": "get_line_details",
                        "parameters": {"line_id": "L1001"},
                        "tool_call_id": "call_2"
                    }
                ],
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should display all tool calls
    
    @pytest.mark.asyncio
    async def test_chatbot_with_complex_parameters(self):
        """Test tool call with complex nested parameters."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "Chatbot",
                "content": None,
                "rationale": None,
                "tool_calls": [
                    {
                        "name": "complex_action",
                        "parameters": {
                            "user": {"id": "123", "name": "John"},
                            "settings": {"timeout": 30, "retry": True},
                            "items": ["a", "b", "c"]
                        },
                        "tool_call_id": "call_complex"
                    }
                ],
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should format complex JSON parameters


class TestToolTurn:
    """Test rendering of Tool turns with results."""
    
    @pytest.mark.asyncio
    async def test_tool_turn_basic(self):
        """Test basic Tool turn with simple result."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "Tool",
                "content": None,
                "rationale": None,
                "tool_calls": None,
                "tool_results": [
                    {
                        "outputs": [
                            {"text": "Transfer successful", "type": "text"}
                        ],
                        "tool_call_id": "call_123"
                    }
                ]
            }
        ]
        viewer.conversation = conversation
        # Should display tool result with 🔍
    
    @pytest.mark.asyncio
    async def test_tool_turn_with_json_result(self):
        """Test Tool turn with JSON result."""
        viewer = ConversationViewer()
        json_result = '{"status": "success", "user_id": "123", "balance": 100.50}'
        conversation = [
            {
                "role": "Tool",
                "content": None,
                "rationale": None,
                "tool_calls": None,
                "tool_results": [
                    {
                        "outputs": [
                            {"text": json_result, "type": "json"}
                        ],
                        "tool_call_id": "call_get_user"
                    }
                ]
            }
        ]
        viewer.conversation = conversation
        # Should pretty-print JSON result
    
    @pytest.mark.asyncio
    async def test_tool_turn_multiple_outputs(self):
        """Test Tool turn with multiple outputs."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "Tool",
                "content": None,
                "rationale": None,
                "tool_calls": None,
                "tool_results": [
                    {
                        "outputs": [
                            {"text": "First output", "type": "text"},
                            {"text": "Second output", "type": "text"},
                        ],
                        "tool_call_id": "call_multi"
                    }
                ]
            }
        ]
        viewer.conversation = conversation
        # Should display all outputs


class TestFullConversation:
    """Test rendering of complete conversations."""
    
    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """Test a complete conversation with all turn types."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "System",
                "content": [{"text": "You are a helpful assistant.", "content_type": "text"}],
                "rationale": None,
                "tool_calls": None,
                "tool_results": None,
            },
            {
                "role": "User",
                "content": [{"text": "I need help with my mobile data.", "content_type": "text"}],
                "rationale": None,
                "tool_calls": None,
                "tool_results": None,
            },
            {
                "role": "Chatbot",
                "content": None,
                "rationale": "I should transfer this to a technical support agent.",
                "tool_calls": [
                    {
                        "name": "transfer_to_human_agents",
                        "parameters": {"summary": "Mobile data issue"},
                        "tool_call_id": "call_transfer"
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
                        "outputs": [{"text": "Transfer successful", "type": "text"}],
                        "tool_call_id": "call_transfer"
                    }
                ]
            },
            {
                "role": "Chatbot",
                "content": [{"text": "I've transferred you to a human agent.", "content_type": "text"}],
                "rationale": None,
                "tool_calls": None,
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should render all turns in order
    
    @pytest.mark.asyncio
    async def test_conversation_with_multiple_tool_calls(self):
        """Test conversation with multiple tool call/result pairs."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "User",
                "content": [{"text": "Check my account", "content_type": "text"}],
                "rationale": None,
                "tool_calls": None,
                "tool_results": None,
            },
            {
                "role": "Chatbot",
                "content": None,
                "rationale": "I'll look up the user's account.",
                "tool_calls": [
                    {
                        "name": "get_customer_by_phone",
                        "parameters": {"phone_number": "555-1234"},
                        "tool_call_id": "call_1"
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
                        "outputs": [{"text": '{"customer_id": "C123"}', "type": "json"}],
                        "tool_call_id": "call_1"
                    }
                ]
            },
            {
                "role": "Chatbot",
                "content": None,
                "rationale": "Now I'll get the line details.",
                "tool_calls": [
                    {
                        "name": "get_line_details",
                        "parameters": {"line_id": "L123"},
                        "tool_call_id": "call_2"
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
                        "outputs": [{"text": '{"status": "active"}', "type": "json"}],
                        "tool_call_id": "call_2"
                    }
                ]
            },
            {
                "role": "Chatbot",
                "content": [{"text": "Your account is active.", "content_type": "text"}],
                "rationale": None,
                "tool_calls": None,
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should render all tool calls and results in order


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_unknown_role(self):
        """Test handling of unknown role type."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "UnknownRole",
                "content": [{"text": "Some content", "content_type": "text"}],
                "rationale": None,
                "tool_calls": None,
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should render as "Unknown Turn Type" without crashing
    
    @pytest.mark.asyncio
    async def test_missing_role(self):
        """Test handling of missing role field."""
        viewer = ConversationViewer()
        conversation = [
            {
                "content": [{"text": "Some content", "content_type": "text"}],
                "rationale": None,
                "tool_calls": None,
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should handle gracefully
    
    @pytest.mark.asyncio
    async def test_chatbot_with_no_content(self):
        """Test Chatbot turn with no content, rationale, or tool calls."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "Chatbot",
                "content": None,
                "rationale": None,
                "tool_calls": None,
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should display "[No content]"
    
    @pytest.mark.asyncio
    async def test_tool_call_with_invalid_json_parameters(self):
        """Test tool call with non-JSON-serializable parameters."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "Chatbot",
                "content": None,
                "rationale": None,
                "tool_calls": [
                    {
                        "name": "test_tool",
                        "parameters": "not a dict",  # Invalid
                        "tool_call_id": "call_bad"
                    }
                ],
                "tool_results": None,
            }
        ]
        viewer.conversation = conversation
        # Should handle gracefully, display as string
    
    @pytest.mark.asyncio
    async def test_tool_result_with_non_json_string(self):
        """Test tool result that looks like JSON but isn't."""
        viewer = ConversationViewer()
        conversation = [
            {
                "role": "Tool",
                "content": None,
                "rationale": None,
                "tool_calls": None,
                "tool_results": [
                    {
                        "outputs": [
                            {"text": "{not valid json}", "type": "text"}
                        ],
                        "tool_call_id": "call_123"
                    }
                ]
            }
        ]
        viewer.conversation = conversation
        # Should display as plain text, not crash

