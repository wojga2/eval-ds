"""
Widgets for the Bee Sample Viewer TUI.
"""

import json
import re
from typing import Any, Optional, Dict, List, Tuple
from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.binding import Binding
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.console import Group
from rich.text import Text
from rich.table import Table as RichTable
from rich.panel import Panel
from rich.rule import Rule


class SampleList(DataTable):
    """Table showing list of samples with key information."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True


class SampleDetail(Static):
    """Detailed view of a single sample."""
    
    sample: reactive[Optional[Dict[str, Any]]] = reactive(None)
    
    def watch_sample(self, sample: Optional[Dict[str, Any]]) -> None:
        """Update the display when sample changes."""
        if sample:
            self.update(self.render_sample(sample))
        else:
            self.update("No sample selected")
    
    def render_sample(self, sample: Dict[str, Any]) -> RichTable:
        """Render sample information in a nice table."""
        table = RichTable(title="Sample Details", show_header=False, box=None)
        table.add_column("Field", style="cyan bold", width=20)
        table.add_column("Value", style="white")
        
        # Key fields
        table.add_row("Sample ID", str(sample.get("sample_id", "N/A"))[:14] + "…")
        table.add_row("Task", str(sample.get("task_name", "N/A"))[:14] + "…")
        table.add_row("Created", str(sample.get("created_at", "N/A"))[:14] + "…")
        
        # Metrics summary
        metrics = sample.get("metrics", {})
        if metrics:
            metrics_str = ", ".join([f"{k}: {v}" for k, v in list(metrics.items())[:5]])
            table.add_row("Metrics", metrics_str)
        
        # Check what fields are available
        has_inputs = sample.get("inputs") is not None
        has_outputs = sample.get("outputs") is not None
        has_debug = sample.get("debug_info") is not None
        
        availability = []
        if has_outputs:
            availability.append("[green]✓ outputs[/green]")
        if has_inputs:
            availability.append("[green]✓ inputs[/green]")
        else:
            availability.append("[red]✗ inputs[/red]")
        if has_debug:
            availability.append("[green]✓ debug_info[/green]")
        
        table.add_row("Available", " | ".join(availability))
        
        return table


class JSONViewer(ScrollableContainer):
    """JSON viewer with markdown support and toggle."""
    
    # Make it focusable for keyboard scrolling
    can_focus = True
    
    # Note: 'm' binding is handled at app level for global access
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data = None
        self._content_widget = None
        self._markdown_mode = False  # Start with JSON mode
    
    def compose(self) -> ComposeResult:
        """Compose the widget with a Static child for content."""
        self._content_widget = Static("[dim]Loading...[/dim]", id="content")
        yield self._content_widget
    
    def on_mount(self) -> None:
        """Called when widget is mounted - update content if we have data."""
        if self._data is not None:
            self._update_content()
    
    @property
    def data(self) -> Optional[Any]:
        return self._data
    
    @data.setter
    def data(self, value: Any) -> None:
        """Update display when data changes."""
        self._data = value
        # Only update if the widget is mounted
        if self.is_mounted and self._content_widget is not None:
            self._update_content()
    
    @property
    def markdown_mode(self) -> bool:
        """Get markdown mode status."""
        return self._markdown_mode
    
    def action_toggle_markdown(self) -> None:
        """Toggle between markdown and JSON view."""
        self._markdown_mode = not self._markdown_mode
        self._update_content()
        mode_str = "Markdown" if self._markdown_mode else "JSON"
        self.app.notify(f"View mode: {mode_str}", timeout=2)
    
    def _update_content(self) -> None:
        """Update the content display."""
        if self._content_widget is None:
            return
            
        try:
            if self._data is None:
                self._content_widget.update("[dim]No data[/dim]")
                return
            
            if not isinstance(self._data, (dict, list)):
                self._content_widget.update(str(self._data))
                return
            
            # Check if we should render as markdown
            if self._markdown_mode and self._has_markdown_content(self._data):
                # Render with markdown formatting
                rendered = self._render_markdown(self._data)
                self._content_widget.update(rendered)
            else:
                # Always show full JSON with word wrap - no truncation
                json_str = json.dumps(self._data, indent=2, default=str)
                syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True, word_wrap=True)
                self._content_widget.update(syntax)
            
        except Exception as e:
            self._content_widget.update(f"[red]Error: {e}[/red]")
    
    def _has_markdown_content(self, data: Any) -> bool:
        """Check if the data contains markdown-rich content (recursively)."""
        if isinstance(data, str):
            # Check if this string has markdown indicators
            if len(data) > 100:
                if any(indicator in data for indicator in ['##', '```', '**', '- ', '\n#', '<|']):
                    return True
        elif isinstance(data, dict):
            # Recursively check all values in the dict
            for value in data.values():
                if self._has_markdown_content(value):
                    return True
        elif isinstance(data, list):
            # Recursively check all items in the list
            for item in data:
                if self._has_markdown_content(item):
                    return True
        return False
    
    def _render_markdown(self, data: dict) -> Group:
        """Render data with markdown formatting for text-heavy fields."""
        elements = []
        
        for key, value in data.items():
            # Header for each field
            header = Text(f"━━ {key} ", style="bold cyan")
            elements.append(header)
            elements.append(Text(""))  # Spacing
            
            rendered = self._render_value(value)
            elements.append(rendered)
            elements.append(Text(""))  # Spacing between fields
        
        return Group(*elements)
    
    def _render_value(self, value: Any) -> Any:
        """Render a single value (handles nested structures recursively)."""
        if value is None:
            return Text("null", style="dim")
        
        elif isinstance(value, str):
            # Check if it's a large string
            if len(value) > 100:
                # Check if it looks like markdown
                if any(indicator in value for indicator in ['##', '```', '**', '- ', '\n#', '<|']):
                    return self._render_markdown_with_code(value)
                # Check if it's JSON
                elif self._looks_like_json(value):
                    return self._render_json_string(value)
            # Short string or plain text
            return Text(value, style="white")
        
        elif isinstance(value, dict):
            # Recursively render nested dict
            nested_elements = []
            for k, v in value.items():
                nested_elements.append(Text(f"  {k}: ", style="cyan"))
                rendered_v = self._render_value(v)
                nested_elements.append(rendered_v)
                nested_elements.append(Text(""))
            return Group(*nested_elements)
        
        elif isinstance(value, list):
            # Show nested list
            if all(isinstance(item, (str, int, float, bool)) for item in value):
                # Simple list - show as JSON
                json_str = json.dumps(value, indent=2, default=str)
                return Syntax(json_str, "json", theme="monokai", word_wrap=True)
            else:
                # Complex list - render each item
                list_elements = []
                for i, item in enumerate(value):
                    list_elements.append(Text(f"  [{i}]: ", style="dim"))
                    list_elements.append(self._render_value(item))
                    list_elements.append(Text(""))
                return Group(*list_elements)
        
        else:
            return Text(str(value), style="yellow")
    
    def _looks_like_json(self, text: str) -> bool:
        """Check if a string looks like JSON."""
        text = text.strip()
        if (text.startswith('{') and text.endswith('}')) or \
           (text.startswith('[') and text.endswith(']')):
            try:
                json.loads(text)
                return True
            except:
                pass
        return False
    
    def _render_json_string(self, text: str) -> Any:
        """Render a JSON string with proper formatting."""
        try:
            parsed = json.loads(text)
            formatted = json.dumps(parsed, indent=2)
            return Syntax(formatted, "json", theme="monokai", line_numbers=True, word_wrap=True)
        except:
            return Text(text, style="white")
    
    def _parse_token_sections(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Parse text with <|TOKEN|> markers into sections.
        Returns list of (section_type, token_name, content) tuples.
        
        Section types: 'system', 'user', 'chatbot', 'thinking', 'action', 
                      'response', 'tool_result', 'turn', 'plain'
        """
        # Token categories with their display properties
        token_map = {
            '<|SYSTEM_TOKEN|>': 'system',
            '<|USER_TOKEN|>': 'user',
            '<|CHATBOT_TOKEN|>': 'chatbot',
            '<|START_THINKING|>': 'thinking',
            '<|END_THINKING|>': 'end_thinking',
            '<|START_ACTION|>': 'action',
            '<|END_ACTION|>': 'end_action',
            '<|START_RESPONSE|>': 'response',
            '<|END_RESPONSE|>': 'end_response',
            '<|START_TOOL_RESULT|>': 'tool_result',
            '<|END_TOOL_RESULT|>': 'end_tool_result',
            '<|START_OF_TURN_TOKEN|>': 'turn_start',
            '<|END_OF_TURN_TOKEN|>': 'turn_end',
        }
        
        # Find all token positions
        token_pattern = r'<\|[A-Z_]+\|>'
        matches = list(re.finditer(token_pattern, text))
        
        if not matches:
            return [('plain', '', text)]
        
        sections = []
        current_section_type = 'plain'
        current_section_start = 0
        section_stack = []  # Track nested sections
        
        for match in matches:
            token = match.group()
            token_start = match.start()
            token_end = match.end()
            
            # Add content before this token
            if token_start > current_section_start:
                content = text[current_section_start:token_start]
                if content.strip():
                    sections.append((current_section_type, token, content))
            
            # Update current section type
            if token in token_map:
                section_type = token_map[token]
                
                if section_type.startswith('end_'):
                    # Pop from stack
                    if section_stack:
                        section_stack.pop()
                    current_section_type = section_stack[-1] if section_stack else 'plain'
                elif section_type in ['turn_start', 'turn_end']:
                    # Turn markers don't change section type
                    pass
                else:
                    # Push to stack
                    section_stack.append(section_type)
                    current_section_type = section_type
                
                current_section_start = token_end
            else:
                # Unknown token - treat as regular text, don't advance position
                # This ensures unknown tokens are included in the content
                pass
        
        # Add remaining content
        if current_section_start < len(text):
            content = text[current_section_start:]
            if content.strip():
                sections.append((current_section_type, '', content))
        
        return sections if sections else [('plain', '', text)]
    
    def _render_markdown_with_code(self, text: str) -> Group:
        """Render markdown text with properly formatted code blocks and token sections."""
        elements = []
        
        # First, parse token sections
        sections = self._parse_token_sections(text)
        
        for section_type, token, content in sections:
            # Add section header if it's a special section
            if section_type != 'plain':
                header = self._create_section_header(section_type)
                if header:
                    elements.append(header)
            
            # Render the content based on section type
            if not content.strip():
                continue
            
            # For ACTION and TOOL_RESULT sections, try to parse as JSON first
            if section_type in ['action', 'tool_result']:
                json_rendered = self._try_render_as_json(content)
                if json_rendered:
                    if section_type != 'plain':
                        elements.append(self._style_section(section_type, [json_rendered]))
                    else:
                        elements.append(json_rendered)
                    continue
            
            # Otherwise, process code blocks within this section
            section_elements = self._render_text_with_code_blocks(content)
            
            # Wrap in colored panel if special section
            if section_type != 'plain':
                styled_group = self._style_section(section_type, section_elements)
                elements.append(styled_group)
            else:
                elements.extend(section_elements)
        
        return Group(*elements)
    
    def _create_section_header(self, section_type: str) -> Optional[Text]:
        """Create a styled header for a section."""
        headers = {
            'system': ('🔧 SYSTEM', 'bold blue'),
            'user': ('👤 USER', 'bold green'),
            'chatbot': ('🤖 ASSISTANT', 'bold cyan'),
            'thinking': ('💭 THINKING', 'bold yellow'),
            'action': ('⚡ ACTION', 'bold magenta'),
            'response': ('💬 RESPONSE', 'bold cyan'),
            'tool_result': ('🔨 TOOL RESULT', 'bold red'),
        }
        
        if section_type in headers:
            label, style = headers[section_type]
            return Text(f"\n{'─' * 60}\n{label}\n{'─' * 60}\n", style=style)
        return None
    
    def _try_render_as_json(self, text: str) -> Optional[Syntax]:
        """Try to parse and render text as JSON with recursive nested JSON handling."""
        stripped = text.strip()
        if not stripped:
            return None
        
        # Check if it looks like JSON (starts with [ or {)
        if not (stripped.startswith('{') or stripped.startswith('[')):
            return None
        
        try:
            parsed = json.loads(stripped)
            # Recursively expand nested JSON strings
            expanded = self._expand_nested_json(parsed)
            formatted = json.dumps(expanded, indent=2)
            return Syntax(formatted, "json", theme="monokai", 
                         line_numbers=True, word_wrap=True)
        except (json.JSONDecodeError, ValueError):
            return None
    
    def _expand_nested_json(self, obj: Any) -> Any:
        """
        Recursively expand JSON strings within a data structure.
        If a string value is valid JSON, parse it and expand it recursively.
        """
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                result[key] = self._expand_nested_json(value)
            return result
        elif isinstance(obj, list):
            return [self._expand_nested_json(item) for item in obj]
        elif isinstance(obj, str):
            # Check if this string is itself valid JSON
            stripped = obj.strip()
            if len(stripped) > 1 and (stripped.startswith('{') or stripped.startswith('[')):
                try:
                    nested = json.loads(stripped)
                    # Recursively expand this nested JSON too
                    return {
                        "_nested_json_": True,
                        "_content_": self._expand_nested_json(nested)
                    }
                except (json.JSONDecodeError, ValueError):
                    # Not valid JSON, return as-is
                    return obj
            return obj
        else:
            # Numbers, booleans, null, etc.
            return obj
    
    def _style_section(self, section_type: str, elements: List) -> Group:
        """Apply styling to a section's elements."""
        # Add subtle indentation for nested sections
        indent = "  "
        styled_elements = []
        
        for element in elements:
            if isinstance(element, Text):
                # Add indent to each line
                indented = Text()
                for line in str(element).split('\n'):
                    if line:
                        indented.append(indent + line + '\n')
                styled_elements.append(indented)
            else:
                styled_elements.append(element)
        
        return Group(*styled_elements)
    
    def _render_text_with_code_blocks(self, text: str) -> List:
        """Render text with code blocks (helper for _render_markdown_with_code)."""
        elements = []
        
        # Pattern to find code blocks with optional language
        code_block_pattern = r'```(\w+)?\n(.*?)```'
        
        last_end = 0
        for match in re.finditer(code_block_pattern, text, re.DOTALL):
            # Add text before code block as markdown
            before_text = text[last_end:match.start()]
            if before_text.strip():
                try:
                    md = Markdown(before_text)
                    elements.append(md)
                except:
                    elements.append(Text(before_text))
            
            # Extract and format code block
            language = match.group(1) or 'text'
            code_content = match.group(2).strip()
            
            # Special handling for JSON blocks
            if language.lower() == 'json':
                try:
                    # Parse and re-format JSON with proper indentation
                    parsed_json = json.loads(code_content)
                    formatted_json = json.dumps(parsed_json, indent=2)
                    syntax = Syntax(formatted_json, "json", theme="monokai", 
                                   line_numbers=True, word_wrap=True)
                except json.JSONDecodeError:
                    # If parsing fails, just syntax highlight as-is
                    syntax = Syntax(code_content, "json", theme="monokai", 
                                   line_numbers=True, word_wrap=True)
            else:
                # Other languages
                syntax = Syntax(code_content, language, theme="monokai", 
                               line_numbers=True, word_wrap=True)
            
            elements.append(syntax)
            elements.append(Text(""))  # Spacing
            
            last_end = match.end()
        
        # Add remaining text after last code block
        remaining_text = text[last_end:]
        if remaining_text.strip():
            try:
                md = Markdown(remaining_text)
                elements.append(md)
            except:
                elements.append(Text(remaining_text))
        
        return elements
