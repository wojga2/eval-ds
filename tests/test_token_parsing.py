"""
Tests for special token parsing and rendering in the Bee Sample Viewer.

Tests cover all token types found in TauBench data:
- START/END tokens (THINKING, ACTION, RESPONSE, TOOL_RESULT, OF_TURN_TOKEN)
- Role tokens (SYSTEM_TOKEN, USER_TOKEN, CHATBOT_TOKEN)
"""

import pytest
from bee_sample_viewer.widgets import JSONViewer


class TestTokenDetection:
    """Tests for detecting various token types."""
    
    def test_detects_system_token(self):
        """Test detection of SYSTEM_TOKEN."""
        viewer = JSONViewer()
        text = "<|SYSTEM_TOKEN|>You are a helpful assistant."
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) > 0
        assert sections[0][0] == 'system'
    
    def test_detects_user_token(self):
        """Test detection of USER_TOKEN."""
        viewer = JSONViewer()
        text = "<|USER_TOKEN|>What is the weather today?"
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) > 0
        assert sections[0][0] == 'user'
    
    def test_detects_chatbot_token(self):
        """Test detection of CHATBOT_TOKEN."""
        viewer = JSONViewer()
        text = "<|CHATBOT_TOKEN|>Let me help you with that."
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) > 0
        assert sections[0][0] == 'chatbot'
    
    def test_detects_thinking_section(self):
        """Test detection of THINKING section."""
        viewer = JSONViewer()
        text = "<|START_THINKING|>I need to analyze this carefully.<|END_THINKING|>"
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) > 0
        assert sections[0][0] == 'thinking'
    
    def test_detects_action_section(self):
        """Test detection of ACTION section."""
        viewer = JSONViewer()
        text = '<|START_ACTION|>{"tool": "search", "query": "weather"}<|END_ACTION|>'
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) > 0
        assert sections[0][0] == 'action'
    
    def test_detects_response_section(self):
        """Test detection of RESPONSE section."""
        viewer = JSONViewer()
        text = "<|START_RESPONSE|>Here is my answer.<|END_RESPONSE|>"
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) > 0
        assert sections[0][0] == 'response'
    
    def test_detects_tool_result_section(self):
        """Test detection of TOOL_RESULT section."""
        viewer = JSONViewer()
        text = '<|START_TOOL_RESULT|>{"result": "success"}<|END_TOOL_RESULT|>'
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) > 0
        assert sections[0][0] == 'tool_result'
    
    def test_detects_turn_tokens(self):
        """Test detection of TURN tokens."""
        viewer = JSONViewer()
        text = "<|START_OF_TURN_TOKEN|>Hello<|END_OF_TURN_TOKEN|>"
        sections = viewer._parse_token_sections(text)
        
        # Turn tokens don't change section type but are recognized
        assert len(sections) > 0
    
    def test_plain_text_without_tokens(self):
        """Test text without any tokens."""
        viewer = JSONViewer()
        text = "This is just plain text without any special tokens."
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) == 1
        assert sections[0][0] == 'plain'
        assert sections[0][2] == text


class TestComplexTokenPatterns:
    """Tests for complex token patterns and nesting."""
    
    def test_multiple_sections_in_sequence(self):
        """Test multiple different sections in sequence."""
        viewer = JSONViewer()
        text = (
            "<|SYSTEM_TOKEN|>System prompt here."
            "<|USER_TOKEN|>User question here."
            "<|CHATBOT_TOKEN|>Assistant response here."
        )
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) == 3
        assert sections[0][0] == 'system'
        assert sections[1][0] == 'user'
        assert sections[2][0] == 'chatbot'
    
    def test_nested_sections(self):
        """Test nested sections (e.g., thinking inside chatbot)."""
        viewer = JSONViewer()
        text = (
            "<|CHATBOT_TOKEN|>Let me think about this."
            "<|START_THINKING|>I should analyze this carefully.<|END_THINKING|>"
            "Here is my answer."
        )
        sections = viewer._parse_token_sections(text)
        
        # Should have sections for chatbot content and thinking
        assert len(sections) >= 2
        section_types = [s[0] for s in sections]
        assert 'chatbot' in section_types
        assert 'thinking' in section_types
    
    def test_action_with_response(self):
        """Test action followed by tool result and response."""
        viewer = JSONViewer()
        text = (
            '<|START_ACTION|>{"action": "search"}<|END_ACTION|>'
            '<|START_TOOL_RESULT|>{"results": ["item1", "item2"]}<|END_TOOL_RESULT|>'
            '<|START_RESPONSE|>Based on the results...<|END_RESPONSE|>'
        )
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) >= 3
        section_types = [s[0] for s in sections]
        assert 'action' in section_types
        assert 'tool_result' in section_types
        assert 'response' in section_types
    
    def test_multiple_thinking_sections(self):
        """Test multiple thinking sections in sequence."""
        viewer = JSONViewer()
        text = (
            "<|START_THINKING|>First thought.<|END_THINKING|>"
            "Some text."
            "<|START_THINKING|>Second thought.<|END_THINKING|>"
        )
        sections = viewer._parse_token_sections(text)
        
        thinking_sections = [s for s in sections if s[0] == 'thinking']
        assert len(thinking_sections) >= 2
    
    def test_turn_markers_with_content(self):
        """Test turn markers with content between them."""
        viewer = JSONViewer()
        text = (
            "<|START_OF_TURN_TOKEN|>"
            "<|USER_TOKEN|>Hello there!"
            "<|END_OF_TURN_TOKEN|>"
            "<|START_OF_TURN_TOKEN|>"
            "<|CHATBOT_TOKEN|>Hi! How can I help?"
            "<|END_OF_TURN_TOKEN|>"
        )
        sections = viewer._parse_token_sections(text)
        
        section_types = [s[0] for s in sections]
        assert 'user' in section_types
        assert 'chatbot' in section_types
    
    def test_empty_sections(self):
        """Test handling of empty sections."""
        viewer = JSONViewer()
        text = "<|START_THINKING|><|END_THINKING|>Some text."
        sections = viewer._parse_token_sections(text)
        
        # Should not create empty sections
        for section_type, token, content in sections:
            assert content.strip() != ''
    
    def test_whitespace_handling(self):
        """Test proper handling of whitespace around tokens."""
        viewer = JSONViewer()
        text = "  <|USER_TOKEN|>  Question with spaces  "
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) > 0
        # Content should be preserved as-is
        assert 'Question with spaces' in sections[0][2]


class TestSectionHeaders:
    """Tests for section header creation."""
    
    def test_creates_system_header(self):
        """Test system section header."""
        viewer = JSONViewer()
        header = viewer._create_section_header('system')
        
        assert header is not None
        assert 'SYSTEM' in str(header)
    
    def test_creates_user_header(self):
        """Test user section header."""
        viewer = JSONViewer()
        header = viewer._create_section_header('user')
        
        assert header is not None
        assert 'USER' in str(header)
    
    def test_creates_chatbot_header(self):
        """Test chatbot section header."""
        viewer = JSONViewer()
        header = viewer._create_section_header('chatbot')
        
        assert header is not None
        assert 'ASSISTANT' in str(header)
    
    def test_creates_thinking_header(self):
        """Test thinking section header."""
        viewer = JSONViewer()
        header = viewer._create_section_header('thinking')
        
        assert header is not None
        assert 'THINKING' in str(header)
    
    def test_creates_action_header(self):
        """Test action section header."""
        viewer = JSONViewer()
        header = viewer._create_section_header('action')
        
        assert header is not None
        assert 'ACTION' in str(header)
    
    def test_creates_response_header(self):
        """Test response section header."""
        viewer = JSONViewer()
        header = viewer._create_section_header('response')
        
        assert header is not None
        assert 'RESPONSE' in str(header)
    
    def test_creates_tool_result_header(self):
        """Test tool result section header."""
        viewer = JSONViewer()
        header = viewer._create_section_header('tool_result')
        
        assert header is not None
        assert 'TOOL RESULT' in str(header)
    
    def test_no_header_for_plain(self):
        """Test that plain sections don't get headers."""
        viewer = JSONViewer()
        header = viewer._create_section_header('plain')
        
        assert header is None
    
    def test_no_header_for_unknown(self):
        """Test that unknown section types don't get headers."""
        viewer = JSONViewer()
        header = viewer._create_section_header('unknown_type')
        
        assert header is None


class TestRealWorldPatterns:
    """Tests based on actual TauBench data patterns."""
    
    def test_complete_conversation_turn(self):
        """Test a complete conversation turn with all token types."""
        viewer = JSONViewer()
        text = (
            "<|START_OF_TURN_TOKEN|>"
            "<|USER_TOKEN|>I need to search for a product."
            "<|END_OF_TURN_TOKEN|>"
            "<|START_OF_TURN_TOKEN|>"
            "<|CHATBOT_TOKEN|>Let me help you with that. "
            "<|START_THINKING|>The user wants to search. I should use the search tool.<|END_THINKING|>"
            '<|START_ACTION|>{"tool": "search", "parameters": {"query": "product"}}<|END_ACTION|>'
            "<|END_OF_TURN_TOKEN|>"
            "<|START_OF_TURN_TOKEN|>"
            "<|SYSTEM_TOKEN|>"
            '<|START_TOOL_RESULT|>{"results": ["Product A", "Product B"]}<|END_TOOL_RESULT|>'
            "<|END_OF_TURN_TOKEN|>"
            "<|START_OF_TURN_TOKEN|>"
            "<|CHATBOT_TOKEN|>"
            "<|START_RESPONSE|>I found these products for you: Product A and Product B.<|END_RESPONSE|>"
            "<|END_OF_TURN_TOKEN|>"
        )
        sections = viewer._parse_token_sections(text)
        
        # Should parse without errors
        assert len(sections) > 0
        
        # Should detect all major section types
        section_types = [s[0] for s in sections]
        assert 'user' in section_types
        assert 'chatbot' in section_types
        assert 'thinking' in section_types
        assert 'action' in section_types
        assert 'tool_result' in section_types
        assert 'response' in section_types
    
    def test_json_in_action_section(self):
        """Test that JSON within action sections is preserved."""
        viewer = JSONViewer()
        json_content = '{"tool_name": "get_order_details", "parameters": {"order_id": "#W6247578"}}'
        text = f'<|START_ACTION|>{json_content}<|END_ACTION|>'
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) > 0
        assert sections[0][0] == 'action'
        # JSON content should be in the section
        assert 'tool_name' in sections[0][2]
        assert 'get_order_details' in sections[0][2]
    
    def test_markdown_in_response_section(self):
        """Test that markdown within response sections is preserved."""
        viewer = JSONViewer()
        markdown_content = "Here are the **results**:\n- Item 1\n- Item 2"
        text = f'<|START_RESPONSE|>{markdown_content}<|END_RESPONSE|>'
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) > 0
        assert sections[0][0] == 'response'
        # Markdown should be preserved
        assert '**results**' in sections[0][2]
        assert '- Item 1' in sections[0][2]
    
    def test_multiline_thinking(self):
        """Test multi-line thinking sections."""
        viewer = JSONViewer()
        text = (
            "<|START_THINKING|>"
            "I need to consider several factors:\n"
            "1. The user's request\n"
            "2. Available tools\n"
            "3. Expected output format\n"
            "<|END_THINKING|>"
        )
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) > 0
        assert sections[0][0] == 'thinking'
        assert '\n' in sections[0][2]
        assert '1. The user' in sections[0][2]
    
    def test_special_characters_in_content(self):
        """Test content with special characters."""
        viewer = JSONViewer()
        text = '<|USER_TOKEN|>What about items priced at $99.99 & up?'
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) > 0
        assert '$99.99' in sections[0][2]
        assert '&' in sections[0][2]
    
    def test_unicode_in_content(self):
        """Test content with unicode characters."""
        viewer = JSONViewer()
        text = '<|CHATBOT_TOKEN|>Here are the results: 🔍 Search complete! 💡'
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) > 0
        assert '🔍' in sections[0][2]
        assert '💡' in sections[0][2]


class TestEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_empty_string(self):
        """Test handling of empty string."""
        viewer = JSONViewer()
        sections = viewer._parse_token_sections("")
        
        # Should return a single plain section
        assert len(sections) == 1
        assert sections[0][0] == 'plain'
        assert sections[0][2] == ""
    
    def test_only_tokens_no_content(self):
        """Test string with only tokens and no actual content."""
        viewer = JSONViewer()
        text = "<|START_THINKING|><|END_THINKING|>"
        sections = viewer._parse_token_sections(text)
        
        # Should not create sections with empty content
        assert all(s[2].strip() != '' for s in sections) or len(sections) == 0
    
    def test_unclosed_section(self):
        """Test section without closing token."""
        viewer = JSONViewer()
        text = "<|START_THINKING|>This thought is never closed."
        sections = viewer._parse_token_sections(text)
        
        # Should still parse the content
        assert len(sections) > 0
        assert 'This thought is never closed.' in sections[0][2]
    
    def test_mismatched_end_token(self):
        """Test mismatched END token."""
        viewer = JSONViewer()
        text = "<|START_THINKING|>Some thought<|END_ACTION|>"
        sections = viewer._parse_token_sections(text)
        
        # Should handle gracefully
        assert len(sections) > 0
    
    def test_token_at_end_of_string(self):
        """Test token at the very end of string."""
        viewer = JSONViewer()
        text = "Some content here<|USER_TOKEN|>"
        sections = viewer._parse_token_sections(text)
        
        # Should parse without errors
        assert len(sections) > 0
    
    def test_token_at_start_of_string(self):
        """Test token at the very start of string."""
        viewer = JSONViewer()
        text = "<|USER_TOKEN|>Content follows"
        sections = viewer._parse_token_sections(text)
        
        assert len(sections) > 0
        assert sections[0][0] == 'user'
    
    def test_consecutive_tokens(self):
        """Test consecutive tokens without content between."""
        viewer = JSONViewer()
        text = "<|USER_TOKEN|><|CHATBOT_TOKEN|>Response"
        sections = viewer._parse_token_sections(text)
        
        # Should handle consecutive tokens
        assert len(sections) > 0
    
    def test_invalid_token_format(self):
        """Test that invalid token formats are not parsed."""
        viewer = JSONViewer()
        text = "<|INVALID_TOKEN|>This should be plain text"
        sections = viewer._parse_token_sections(text)
        
        # Invalid tokens should be treated as plain text
        assert len(sections) > 0
        # All content should be in plain section(s)
        # The actual content after the invalid token is preserved
        assert any('This should be plain text' in s[2] for s in sections)

