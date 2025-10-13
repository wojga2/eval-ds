"""
Widget for displaying Tau2Bench reward analysis.

This displays:
- Overall reward and pass/fail status
- Expected actions vs actual actions taken
- Natural language assertions
- Environment state checks
- Communication requirements
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from textual.widgets import Static
from textual.containers import ScrollableContainer
from rich.console import Group, RenderableType
from rich.text import Text
from rich.table import Table as RichTable
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax


class RewardViewer(ScrollableContainer):
    """Display detailed analysis of how Tau2Bench reward was calculated."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content_widget: Optional[Static] = None
        self._current_data: Optional[Dict[str, Any]] = None
    
    def compose(self):
        """Create child widgets."""
        self._content_widget = Static("[dim]No sample selected[/dim]", id="content")
        yield self._content_widget
    
    @property
    def data(self) -> Optional[Dict[str, Any]]:
        """Get current sample data."""
        return self._current_data
    
    @data.setter
    def data(self, value: Optional[Dict[str, Any]]) -> None:
        """Set sample data and update display."""
        self._current_data = value
        if self.is_mounted:
            self._update_content()
    
    def on_mount(self):
        """Update content when mounted."""
        if self._current_data:
            self._update_content()
    
    def _update_content(self) -> None:
        """Update the displayed content."""
        if not self._content_widget:
            return
        
        if not self._current_data:
            self._content_widget.update("[dim]No sample data available[/dim]")
            return
        
        try:
            explanation = self._generate_explanation(self._current_data)
            self._content_widget.update(explanation)
        except Exception as e:
            error_text = Text(f"Error generating reward analysis: {str(e)}", style="red")
            self._content_widget.update(error_text)
    
    def _generate_explanation(self, sample: Dict[str, Any]) -> RenderableType:
        """Generate the reward explanation display."""
        renderables = []
        
        # Extract outputs
        outputs = sample.get('outputs', {})
        if not outputs:
            return Text("No reward information available", style="dim")
        
        reward = outputs.get('reward', 'N/A')
        reward_extras = outputs.get('reward_extras') or {}
        reward_metrics = outputs.get('reward_metrics') or {}
        reward_text_info = outputs.get('reward_text_info') or {}
        conversation = outputs.get('conversation') or []
        
        # Header: Overall Status
        status_panel = self._create_status_panel(reward, reward_metrics)
        renderables.append(status_panel)
        renderables.append(Text())  # Blank line
        
        # Section 1: Action Analysis
        action_checks = reward_extras.get('action_checks', [])
        if action_checks:
            action_panel = self._create_action_analysis(action_checks, conversation)
            renderables.append(action_panel)
            renderables.append(Text())
        
        # Section 2: Natural Language Assertions
        nl_assertions = reward_extras.get('nl_assertions', [])
        if nl_assertions:
            nl_panel = self._create_nl_assertions_panel(nl_assertions)
            renderables.append(nl_panel)
            renderables.append(Text())
        
        # Section 3: Reward Breakdown
        metrics_panel = self._create_metrics_panel(reward_metrics, reward_text_info)
        renderables.append(metrics_panel)
        
        return Group(*renderables)
    
    def _create_status_panel(self, reward: Any, metrics: Dict[str, Any]) -> Panel:
        """Create overall status panel."""
        # Determine pass/fail
        is_pass = reward == 1 or reward == 1.0
        status_text = Text()
        
        if is_pass:
            status_text.append("✓ PASS", style="bold green")
        else:
            status_text.append("✗ FAIL", style="bold red")
        
        status_text.append(f" (Reward: {reward})", style="dim")
        
        # Add metrics summary
        if metrics:
            status_text.append("\n\nMetrics:\n", style="bold")
            for key, value in metrics.items():
                metric_name = key.replace('_', ' ').title()
                if value == 1 or value == 1.0:
                    status_text.append(f"  ✓ {metric_name}: ", style="green")
                else:
                    status_text.append(f"  ✗ {metric_name}: ", style="red")
                status_text.append(f"{value}\n")
        
        return Panel(
            status_text,
            title="[bold]Overall Status[/]",
            border_style="cyan",
            padding=(1, 2)
        )
    
    def _create_action_analysis(self, action_checks: List[Dict], conversation: List[Dict]) -> Panel:
        """Create detailed action analysis panel."""
        renderables = []
        
        # Extract actual actions from conversation
        actual_actions = self._extract_actions_from_conversation(conversation)
        
        # Title
        renderables.append(Text("Expected Actions vs Actual Actions", style="bold yellow"))
        renderables.append(Text())
        
        # Create comparison table
        table = RichTable(show_header=True, header_style="bold", box=None)
        table.add_column("Status", width=8)
        table.add_column("Expected Action", style="cyan")
        table.add_column("Arguments", style="dim")
        table.add_column("Match", width=10)
        
        for check in action_checks:
            action_info = check.get('action', {})
            action_match = check.get('action_match', False)
            action_reward = check.get('action_reward', 0)
            
            action_name = action_info.get('name', 'unknown')
            arguments = action_info.get('arguments', {})
            
            # Status icon
            if action_match:
                status = Text("✓", style="green")
                match_text = Text("Yes", style="green")
            else:
                status = Text("✗", style="red")
                match_text = Text("No", style="red")
            
            # Format arguments
            if arguments:
                args_str = ", ".join([f"{k}={v}" for k, v in arguments.items()])
            else:
                args_str = "(no args)"
            
            table.add_row(status, action_name, args_str, match_text)
        
        renderables.append(table)
        renderables.append(Text())
        
        # Show actual actions taken
        if actual_actions:
            renderables.append(Text("Actions Actually Taken:", style="bold"))
            renderables.append(Text())
            for action in actual_actions:
                action_line = Text("  • ", style="dim")
                action_line.append(action['name'], style="magenta")
                if action.get('parameters'):
                    params_str = json.dumps(action['parameters'], ensure_ascii=False)
                    if len(params_str) > 60:
                        params_str = params_str[:60] + "..."
                    action_line.append(f" {params_str}", style="dim")
                renderables.append(action_line)
        else:
            renderables.append(Text("  (No tool calls made)", style="dim italic"))
        
        return Panel(
            Group(*renderables),
            title="[bold]Action Analysis[/]",
            border_style="yellow",
            padding=(1, 2)
        )
    
    def _create_nl_assertions_panel(self, nl_assertions: List[Dict]) -> Panel:
        """Create natural language assertions panel."""
        renderables = []
        
        for assertion in nl_assertions:
            # Extract assertion info
            assertion_text = assertion.get('assertion', 'N/A')
            satisfied = assertion.get('satisfied', False)
            explanation = assertion.get('explanation', '')
            
            # Status
            if satisfied:
                status = Text("✓ ", style="bold green")
            else:
                status = Text("✗ ", style="bold red")
            
            status.append(assertion_text, style="white")
            renderables.append(status)
            
            if explanation:
                renderables.append(Text(f"  {explanation}", style="dim italic"))
            
            renderables.append(Text())  # Blank line
        
        if not renderables:
            renderables.append(Text("No natural language assertions for this task", style="dim"))
        
        return Panel(
            Group(*renderables),
            title="[bold]Natural Language Requirements[/]",
            border_style="blue",
            padding=(1, 2)
        )
    
    def _create_metrics_panel(self, metrics: Dict[str, Any], text_info: Dict[str, Any]) -> Panel:
        """Create reward metrics breakdown panel."""
        renderables = []
        
        # Metrics table
        if metrics:
            table = RichTable(show_header=True, header_style="bold", box=None)
            table.add_column("Metric", style="cyan")
            table.add_column("Score", width=10, justify="right")
            table.add_column("Details", style="dim")
            
            for metric_name, score in metrics.items():
                metric_display = metric_name.replace('_', ' ').title()
                
                # Color code the score
                if score == 1 or score == 1.0:
                    score_text = Text(str(score), style="green")
                elif score == 0:
                    score_text = Text(str(score), style="red")
                else:
                    score_text = Text(str(score), style="yellow")
                
                # Get details from text_info
                details = ""
                if text_info:
                    metric_key = metric_name.lower().replace('_assertion', '')
                    info = text_info.get(metric_key, {})
                    if isinstance(info, dict):
                        note = info.get('note', '')
                        if note:
                            details = note
                
                table.add_row(metric_display, score_text, details)
            
            renderables.append(table)
        else:
            renderables.append(Text("No metrics available", style="dim"))
        
        return Panel(
            Group(*renderables),
            title="[bold]Reward Metrics Breakdown[/]",
            border_style="green",
            padding=(1, 2)
        )
    
    def _extract_actions_from_conversation(self, conversation: List[Dict]) -> List[Dict]:
        """Extract all tool calls (actions) from the conversation."""
        actions = []
        
        for turn in conversation:
            if turn.get('role') == 'Chatbot':
                tool_calls = turn.get('tool_calls', [])
                if tool_calls:
                    for tc in tool_calls:
                        actions.append({
                            'name': tc.get('name', 'unknown'),
                            'parameters': tc.get('parameters', {}),
                            'tool_call_id': tc.get('tool_call_id', '')
                        })
        
        return actions

