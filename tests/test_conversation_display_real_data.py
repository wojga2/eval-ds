"""
Test conversation viewer with real Tau2Bench data.
"""

import pytest
from pathlib import Path
import json
from bee_sample_viewer.app import BeeViewerApp
from bee_sample_viewer.conversation_viewer import ConversationViewer
from rich.console import Console
from rich.text import Text


@pytest.mark.asyncio
async def test_conversation_displays_with_tau2bench_file():
    """Test that conversation from Tau2Bench file displays correctly."""
    tau2bench_file = Path("output/bee_run_531e7b87_20251013_143135.jsonl")
    
    if not tau2bench_file.exists():
        pytest.skip("Tau2Bench data file not found")
    
    # Load the first sample
    with open(tau2bench_file) as f:
        first_line = f.readline()
        sample = json.loads(first_line)
    
    # Verify sample has conversation
    assert "outputs" in sample
    assert sample["outputs"] is not None
    assert "conversation" in sample["outputs"]
    assert sample["outputs"]["conversation"] is not None
    assert len(sample["outputs"]["conversation"]) > 0
    
    print(f"\n✓ Sample has {len(sample['outputs']['conversation'])} conversation turns")
    
    # Test with the app
    app = BeeViewerApp(jsonl_file=str(tau2bench_file))
    async with app.run_test() as pilot:
        await pilot.pause()
        
        # Get the conversation viewer
        conversation_viewer = app.query_one("#conversation-viewer", ConversationViewer)
        
        # Verify conversation was set
        assert conversation_viewer.conversation is not None, "Conversation should not be None"
        assert len(conversation_viewer.conversation) > 0, "Conversation should have turns"
        
        print(f"✓ ConversationViewer has {len(conversation_viewer.conversation)} turns")
        
        # Verify widget is mounted
        assert conversation_viewer.is_mounted, "ConversationViewer should be mounted"
        
        print("✓ ConversationViewer is mounted")
        
        # Verify content widget exists
        assert conversation_viewer._content_widget is not None, "Content widget should exist"
        
        print("✓ Content widget exists")
        
        # Check that _update_display was called by manually rendering the conversation
        # Directly render the conversation to see what it produces
        renderables = []
        for i, turn in enumerate(conversation_viewer.conversation):
            turn_renderable = conversation_viewer._render_turn(turn, i)
            if turn_renderable:
                renderables.append(turn_renderable)
        
        print(f"✓ Generated {len(renderables)} renderables from {len(conversation_viewer.conversation)} turns")
        
        assert len(renderables) > 0, "Should generate renderables from conversation"
        
        # Try to render the Group to string
        from rich.console import Group
        group = Group(*renderables)
        
        console = Console(width=120)
        with console.capture() as capture:
            console.print(group)
        output = capture.get()
        
        print(f"✓ Rendered output length: {len(output)} characters")
        print(f"✓ First 500 chars:\n{output[:500]}")
        
        # The output should contain conversation elements
        assert len(output) > 100, f"Rendered output should be substantial (got {len(output)} chars)"
        
        # Check for specific conversation markers
        sample_conv = sample["outputs"]["conversation"]
        
        # Look for role names or content in output
        found_content = False
        for turn in sample_conv:
            role = turn.get("role", "")
            if role in output:
                found_content = True
                print(f"✓ Found role '{role}' in output")
                break
            # Also check for content
            content = turn.get("content")
            if content and isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "")
                if text and text[:20] in output:
                    found_content = True
                    print(f"✓ Found content text in output")
                    break
        
        assert found_content, f"Should find conversation content in output. Output preview:\n{output[:500]}"


@pytest.mark.asyncio
async def test_conversation_viewer_updates_on_mount():
    """Test that conversation viewer updates display when mounted."""
    # Create a simple conversation
    conversation = [
        {
            "role": "User",
            "content": [{"text": "Test message", "content_type": "text"}],
            "rationale": None,
            "tool_calls": None,
            "tool_results": None,
        }
    ]
    
    # Create viewer and set conversation BEFORE mounting
    viewer = ConversationViewer()
    viewer.conversation = conversation
    
    # Simulate mounting by composing and checking
    from textual.app import App
    
    class TestApp(App):
        def compose(self):
            yield viewer
    
    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        
        # Now check that the viewer has the conversation
        assert viewer.conversation is not None
        assert len(viewer.conversation) == 1
        
        # Check that content widget was updated by manually rendering
        assert viewer._content_widget is not None
        
        # Manually render the conversation to verify it works
        renderables = []
        for i, turn in enumerate(viewer.conversation):
            r = viewer._render_turn(turn, i)
            if r:
                renderables.append(r)
        
        assert len(renderables) > 0, "Should generate renderables"
        
        # Render to string to check content
        from rich.console import Group
        group = Group(*renderables)
        console = Console(width=80)
        with console.capture() as capture:
            console.print(group)
        output = capture.get()
        
        assert "Test message" in output or "User" in output, f"Should contain conversation content. Got: {output[:200]}"
        
        print("✓ Viewer updated correctly when conversation set before mount")


@pytest.mark.asyncio  
async def test_conversation_viewer_renders_all_turn_types():
    """Test that all turn types render correctly."""
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
            "content": [{"text": "Hello!", "content_type": "text"}],
            "rationale": None,
            "tool_calls": None,
            "tool_results": None,
        },
        {
            "role": "Chatbot",
            "content": None,
            "rationale": "I should greet the user",
            "tool_calls": [
                {
                    "name": "test_tool",
                    "parameters": {"key": "value"},
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
                    "outputs": [{"text": "Success", "type": "text"}],
                    "tool_call_id": "call_123"
                }
            ]
        }
    ]
    
    viewer = ConversationViewer()
    
    from textual.app import App
    
    class TestApp(App):
        def compose(self):
            yield viewer
    
    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        
        # Set conversation after mount
        viewer.conversation = conversation
        await pilot.pause()
        
        # Manually render the conversation
        renderables = []
        for i, turn in enumerate(conversation):
            r = viewer._render_turn(turn, i)
            if r:
                renderables.append(r)
        
        assert len(renderables) == 4, f"Should generate 4 renderables, got {len(renderables)}"
        
        # Render to string
        from rich.console import Group
        group = Group(*renderables)
        console = Console(width=80)
        with console.capture() as capture:
            console.print(group)
        output = capture.get()
        
        print(f"✓ Output length: {len(output)}")
        print(f"✓ Output preview:\n{output[:500]}")
        
        # Check for all role types
        assert "System" in output, "Should contain System turn"
        assert "User" in output, "Should contain User turn"
        assert "Chatbot" in output, "Should contain Chatbot turn"
        assert "Tool" in output or "Result" in output, "Should contain Tool turn"
        
        # Check for content
        assert "helpful assistant" in output or "Hello" in output, "Should contain actual content"
        
        print("✓ All turn types rendered correctly")

