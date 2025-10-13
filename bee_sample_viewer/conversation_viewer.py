"""
ConversationViewer widget for displaying FATUC-format conversations from BeeDB.

This displays the standard conversation format used by all BeeDB logs:
- System/User/Chatbot/Tool turns
- Thinking/rationale
- Tool calls and results
- Content
"""

from typing import Any, Dict, List, Optional
from textual.widgets import Static
from textual.containers import ScrollableContainer
from rich.console import Group
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.markdown import Markdown
import json


class ConversationViewer(ScrollableContainer):
    """Widget to display a FATUC conversation with nice formatting."""
    
    # Make it focusable for keyboard scrolling
    can_focus = True
    
    def __init__(self, **kwargs):
        """Initialize the conversation viewer."""
        super().__init__(**kwargs)
        self._content_widget: Optional[Static] = None
        self._conversation: Optional[List[Dict[str, Any]]] = None
    
    def compose(self):
        """Create child widgets."""
        self._content_widget = Static("[dim]Loading conversation...[/dim]", id="content")
        yield self._content_widget
    
    def on_mount(self):
        """Called when the widget is mounted."""
        # Update display if conversation was set before mounting
        if self._conversation is not None:
            self._update_display()
    
    @property
    def conversation(self) -> Optional[List[Dict[str, Any]]]:
        """Get the current conversation."""
        return self._conversation
    
    @conversation.setter
    def conversation(self, value: Optional[List[Dict[str, Any]]]):
        """Set the conversation and update the display."""
        self._conversation = value
        # Only update if widget is mounted
        if self.is_mounted:
            self._update_display()
    
    def _update_display(self):
        """Update the conversation display."""
        if not self._content_widget:
            return
        
        if not self._conversation:
            self._content_widget.update("No conversation data")
            return
        
        renderables = []
        for i, turn in enumerate(self._conversation):
            turn_renderable = self._render_turn(turn, i)
            if turn_renderable:
                renderables.append(turn_renderable)
        
        if renderables:
            group = Group(*renderables)
            self._content_widget.update(group)
            # Refresh to ensure display is updated and scroll to top
            if self.is_mounted and self._content_widget.is_mounted:
                self.refresh(layout=True)
                # Scroll to top to ensure content is visible
                self.call_after_refresh(self.scroll_home)
        else:
            self._content_widget.update("Empty conversation")
    
    def _render_turn(self, turn: Dict[str, Any], index: int) -> Optional[Panel]:
        """Render a single conversation turn."""
        role = turn.get("role", "Unknown")
        
        if role == "System":
            return self._render_system_turn(turn, index)
        elif role == "User":
            return self._render_user_turn(turn, index)
        elif role == "Chatbot":
            return self._render_chatbot_turn(turn, index)
        elif role == "Tool":
            return self._render_tool_turn(turn, index)
        else:
            return self._render_unknown_turn(turn, index)
    
    def _render_system_turn(self, turn: Dict[str, Any], index: int) -> Panel:
        """Render a System turn."""
        content = self._extract_content_text(turn.get("content"))
        
        # System messages are often very long (policy docs), so truncate for display
        if len(content) > 500:
            content = content[:500] + "\n\n... [truncated, full content available in raw data]"
        
        text = Text(content, style="dim")
        
        return Panel(
            text,
            title=f"[bold cyan]System[/] [dim](Turn {index})[/]",
            border_style="cyan",
            padding=(1, 2),
        )
    
    def _render_user_turn(self, turn: Dict[str, Any], index: int) -> Panel:
        """Render a User turn."""
        content = self._extract_content_text(turn.get("content"))
        text = Text(content, style="blue")
        
        return Panel(
            text,
            title=f"[bold blue]User[/] [dim](Turn {index})[/]",
            border_style="blue",
            padding=(1, 2),
        )
    
    def _render_chatbot_turn(self, turn: Dict[str, Any], index: int) -> Panel:
        """Render a Chatbot turn with thinking, tool calls, and/or content."""
        renderables = []
        
        # Thinking/Rationale
        rationale = turn.get("rationale")
        if rationale:
            thinking_text = Text("💭 Thinking:\n", style="italic yellow")
            thinking_text.append(rationale, style="dim")
            renderables.append(thinking_text)
            renderables.append(Text())  # Blank line
        
        # Tool calls
        tool_calls = turn.get("tool_calls")
        if tool_calls:
            for tc in tool_calls:
                tc_title = Text("🔧 Tool Call: ", style="bold magenta")
                tc_title.append(tc.get("name", "unknown"), style="magenta")
                renderables.append(tc_title)
                
                params = tc.get("parameters", {})
                if params:
                    try:
                        params_syntax = self._format_json_with_syntax(params)
                        renderables.append(params_syntax)
                    except:
                        renderables.append(Text(str(params), style="dim"))
                
                renderables.append(Text())  # Blank line
        
        # Content (response)
        content = self._extract_content_text(turn.get("content"))
        if content:
            response_text = Text("💬 Response:\n", style="italic green")
            response_text.append(content, style="green")
            renderables.append(response_text)
        
        # If nothing was rendered, show a placeholder
        if not renderables:
            renderables.append(Text("[No content]", style="dim"))
        
        return Panel(
            Group(*renderables),
            title=f"[bold green]Chatbot[/] [dim](Turn {index})[/]",
            border_style="green",
            padding=(1, 2),
        )
    
    def _render_tool_turn(self, turn: Dict[str, Any], index: int) -> Panel:
        """Render a Tool turn with tool results."""
        renderables = []
        
        tool_results = turn.get("tool_results", [])
        for tr in tool_results:
            tool_call_id = tr.get("tool_call_id", "unknown")
            renderables.append(Text(f"🔍 Result for: {tool_call_id}", style="bold yellow"))
            
            outputs = tr.get("outputs", [])
            for output in outputs:
                if isinstance(output, dict):
                    text_content = output.get("text", "")
                    output_type = output.get("type", "unknown")
                    
                    # Try to format as JSON if it looks like JSON
                    if text_content and self._looks_like_json(text_content):
                        try:
                            parsed = json.loads(text_content)
                            syntax = self._format_json_with_syntax(parsed)
                            renderables.append(syntax)
                        except:
                            renderables.append(Text(text_content, style="yellow"))
                    elif text_content:
                        renderables.append(Text(text_content, style="yellow"))
                    else:
                        # If no text field, try to format the whole output dict as JSON
                        try:
                            syntax = self._format_json_with_syntax(output)
                            renderables.append(syntax)
                        except:
                            renderables.append(Text(str(output), style="yellow"))
                else:
                    renderables.append(Text(str(output), style="yellow"))
            
            renderables.append(Text())  # Blank line
        
        if not renderables:
            renderables.append(Text("[No tool results]", style="dim"))
        
        return Panel(
            Group(*renderables),
            title=f"[bold yellow]Tool Results[/] [dim](Turn {index})[/]",
            border_style="yellow",
            padding=(1, 2),
        )
    
    def _render_unknown_turn(self, turn: Dict[str, Any], index: int) -> Panel:
        """Render an unknown turn type."""
        try:
            content = json.dumps(turn, indent=2)
            syntax = Syntax(content, "json", theme="monokai", line_numbers=False)
            return Panel(
                syntax,
                title=f"[bold red]Unknown Turn Type[/] [dim](Turn {index})[/]",
                border_style="red",
                padding=(1, 2),
            )
        except:
            return Panel(
                Text(str(turn), style="red"),
                title=f"[bold red]Unknown Turn Type[/] [dim](Turn {index})[/]",
                border_style="red",
                padding=(1, 2),
            )
    
    def _extract_content_text(self, content: Any) -> str:
        """Extract text from content field."""
        if not content:
            return ""
        
        if isinstance(content, str):
            return content
        
        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text", "")
                    if text:
                        texts.append(text)
                elif isinstance(item, str):
                    texts.append(item)
            return "\n".join(texts)
        
        if isinstance(content, dict):
            return content.get("text", str(content))
        
        return str(content)
    
    def _looks_like_json(self, text: str) -> bool:
        """Check if text looks like JSON."""
        if not text:
            return False
        
        text = text.strip()
        return (text.startswith('{') and text.endswith('}')) or \
               (text.startswith('[') and text.endswith(']'))
    
    def _expand_nested_json(self, obj: Any, max_depth: int = 5) -> Any:
        """
        Recursively expand nested JSON strings.
        
        If a string value is valid JSON, parse it and continue expanding.
        This handles cases where tool results contain JSON strings that themselves
        contain more JSON strings.
        """
        if max_depth <= 0:
            return obj
        
        if isinstance(obj, str):
            # Try to parse as JSON
            if self._looks_like_json(obj):
                try:
                    parsed = json.loads(obj)
                    # Recursively expand the parsed object
                    return self._expand_nested_json(parsed, max_depth - 1)
                except (json.JSONDecodeError, ValueError):
                    pass
            return obj
        
        elif isinstance(obj, dict):
            return {k: self._expand_nested_json(v, max_depth - 1) for k, v in obj.items()}
        
        elif isinstance(obj, list):
            return [self._expand_nested_json(item, max_depth - 1) for item in obj]
        
        else:
            return obj
    
    def _format_json_with_syntax(self, data: Any, indent: int = 2) -> Syntax:
        """Format data as JSON with syntax highlighting."""
        # Expand nested JSON strings first
        expanded = self._expand_nested_json(data)
        
        # Convert to formatted JSON string
        json_str = json.dumps(expanded, indent=indent, ensure_ascii=False)
        
        # Create syntax-highlighted version
        return Syntax(
            json_str,
            "json",
            theme="monokai",
            line_numbers=False,
            word_wrap=True,
            indent_guides=True,
        )

