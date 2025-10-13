"""
Widget for displaying TauBench reward explanation.
"""

import json
from typing import Any, Dict, List, Optional
from textual.widgets import Static
from textual.containers import ScrollableContainer
from rich.console import Group, RenderableType
from rich.text import Text
from rich.table import Table as RichTable
from rich.panel import Panel
from rich.rule import Rule


class RewardExplanationViewer(ScrollableContainer):
    """Display explanation of how TauBench reward was calculated."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content_widget: Optional[Static] = None
        self._current_data: Optional[Dict[str, Any]] = None
    
    def compose(self):
        """Create child widgets."""
        self._content_widget = Static()
        yield self._content_widget
    
    @property
    def data(self) -> Optional[Dict[str, Any]]:
        """Get current sample data."""
        return self._current_data
    
    @data.setter
    def data(self, value: Optional[Dict[str, Any]]) -> None:
        """Set sample data and update display."""
        self._current_data = value
        self._update_content()
    
    def _update_content(self) -> None:
        """Update the displayed content."""
        if not self._content_widget:
            return
        
        if not self._current_data:
            self._content_widget.update("No sample data available")
            return
        
        try:
            explanation = self._generate_explanation(self._current_data)
            self._content_widget.update(explanation)
        except Exception as e:
            self._content_widget.update(f"Error generating explanation: {e}")
    
    def _generate_explanation(self, sample: Dict[str, Any]) -> RenderableType:
        """Generate the reward explanation display."""
        renderables = []
        
        # Extract data
        metrics = sample.get('metrics', {})
        reward = metrics.get('mean_reward', 0.0)
        expect_no_op = metrics.get('expect_no_op', False)
        
        # Try to get reward info from inputs.metadata
        inputs = sample.get('inputs', {})
        metadata = inputs.get('metadata', {})
        info_str = metadata.get('info')
        
        if not info_str:
            renderables.append(Text("No reward information available for this sample.", style="yellow"))
            return Group(*renderables)
        
        try:
            info = json.loads(info_str) if isinstance(info_str, str) else info_str
        except json.JSONDecodeError:
            renderables.append(Text("Could not parse reward information.", style="red"))
            return Group(*renderables)
        
        # Extract components
        task = info.get('task', {})
        reward_info = info.get('reward_info', {})
        
        # 1. Header with verdict
        verdict_text = self._create_verdict_header(reward, expect_no_op)
        renderables.append(verdict_text)
        renderables.append(Text(""))
        
        # 2. Task instruction
        instruction = task.get('instruction', 'N/A')
        inst_panel = Panel(
            Text(instruction, style="white"),
            title="[cyan bold]Task Instruction[/cyan bold]",
            border_style="cyan"
        )
        renderables.append(inst_panel)
        renderables.append(Text(""))
        
        # 3. Expected vs Actual Actions (DB-mutating only)
        gt_actions = task.get('actions', [])
        actual_actions = reward_info.get('actions', [])
        
        # Filter out RESPOND actions
        gt_actions_filtered = self._filter_db_actions(gt_actions)
        actual_actions_filtered = self._filter_db_actions(actual_actions)
        
        actions_table = self._create_actions_comparison(gt_actions_filtered, actual_actions_filtered)
        renderables.append(actions_table)
        renderables.append(Text(""))
        
        # 4. Required outputs check (if applicable)
        required_outputs = task.get('outputs', [])
        if required_outputs:
            outputs_panel = self._create_outputs_check(required_outputs, reward_info)
            renderables.append(outputs_panel)
            renderables.append(Text(""))
        
        # 5. Diagnostic information
        diagnostic = self._create_diagnostic_info(reward_info, expect_no_op)
        renderables.append(diagnostic)
        
        return Group(*renderables)
    
    def _create_verdict_header(self, reward: float, expect_no_op: bool) -> RenderableType:
        """Create the verdict header showing pass/fail."""
        if reward >= 1.0:
            verdict = Text("✅ TASK PASSED", style="bold green")
            explanation = Text("The agent achieved the correct database state", style="green")
            if expect_no_op:
                explanation.append(" (correctly did nothing)", style="green italic")
        elif reward > 0.0:
            verdict = Text("⚠️  PARTIAL SUCCESS", style="bold yellow")
            explanation = Text(f"Partial reward: {reward:.2f}", style="yellow")
        else:
            verdict = Text("❌ TASK FAILED", style="bold red")
            if expect_no_op:
                explanation = Text("The agent should not have modified the database", style="red")
            else:
                explanation = Text("The final database state did not match the expected state", style="red")
        
        header = Text()
        header.append(verdict)
        header.append("\n")
        header.append(explanation)
        
        return Panel(header, border_style="bold")
    
    def _filter_db_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter to only database-mutating actions (exclude RESPOND)."""
        return [a for a in actions if a.get('name', '').lower() != 'respond']
    
    def _create_actions_comparison(
        self, 
        expected: List[Dict[str, Any]], 
        actual: List[Dict[str, Any]]
    ) -> RenderableType:
        """Create a comparison table of expected vs actual actions."""
        table = RichTable(title="Database Actions Comparison", 
                         show_header=True, 
                         header_style="bold cyan",
                         border_style="cyan")
        table.add_column("Step", style="dim", width=6)
        table.add_column("Expected Actions", style="green", no_wrap=False)
        table.add_column("Actual Actions", style="yellow", no_wrap=False)
        table.add_column("Match", style="white", width=8)
        
        max_len = max(len(expected), len(actual))
        
        for i in range(max_len):
            step = str(i + 1)
            
            # Expected action
            if i < len(expected):
                exp_action = expected[i]
                exp_str = self._format_action(exp_action)
            else:
                exp_str = Text("—", style="dim")
            
            # Actual action
            if i < len(actual):
                act_action = actual[i]
                act_str = self._format_action(act_action)
            else:
                act_str = Text("—", style="dim")
            
            # Check if they match
            if i < len(expected) and i < len(actual):
                if self._actions_match(expected[i], actual[i]):
                    match = Text("✓", style="green bold")
                else:
                    match = Text("✗", style="red bold")
            elif i >= len(expected) and i < len(actual):
                match = Text("Extra", style="yellow")
            elif i < len(expected) and i >= len(actual):
                match = Text("Missing", style="red")
            else:
                match = Text("—", style="dim")
            
            table.add_row(step, exp_str, act_str, match)
        
        # Summary row
        if len(expected) != len(actual):
            table.add_row(
                "",
                Text(f"Total: {len(expected)}", style="bold green"),
                Text(f"Total: {len(actual)}", style="bold yellow"),
                ""
            )
        
        return table
    
    def _format_action(self, action: Dict[str, Any]) -> Text:
        """Format an action for display."""
        name = action.get('name', 'unknown')
        kwargs = action.get('kwargs', {})
        
        text = Text()
        text.append(name, style="bold")
        text.append("(")
        
        # Format kwargs compactly
        if kwargs:
            params = []
            for key, value in kwargs.items():
                if isinstance(value, list):
                    if len(value) <= 3:
                        val_str = str(value)
                    else:
                        val_str = f"[...{len(value)} items]"
                elif isinstance(value, str) and len(value) > 20:
                    val_str = f'"{value[:17]}..."'
                else:
                    val_str = json.dumps(value)
                params.append(f"{key}={val_str}")
            text.append(", ".join(params), style="dim")
        
        text.append(")")
        return text
    
    def _actions_match(self, action1: Dict[str, Any], action2: Dict[str, Any]) -> bool:
        """Check if two actions are equivalent."""
        return (action1.get('name') == action2.get('name') and 
                action1.get('kwargs') == action2.get('kwargs'))
    
    def _create_outputs_check(
        self, 
        required_outputs: List[str], 
        reward_info: Dict[str, Any]
    ) -> RenderableType:
        """Create a panel showing required outputs check."""
        info = reward_info.get('info', {})
        outputs_result = info.get('outputs', {})
        r_outputs = info.get('r_outputs', 0.0)
        
        table = RichTable(show_header=True, header_style="bold cyan", border_style="cyan")
        table.add_column("Required Output", style="white")
        table.add_column("Communicated?", style="white", width=15)
        
        for output in required_outputs:
            found = outputs_result.get(output, False)
            if found:
                status = Text("✓ Yes", style="green bold")
            else:
                status = Text("✗ No", style="red bold")
            table.add_row(output, status)
        
        title_style = "green" if r_outputs >= 1.0 else "red"
        panel = Panel(
            table,
            title=f"[{title_style} bold]Required Outputs Check[/{title_style} bold]",
            border_style=title_style
        )
        return panel
    
    def _create_diagnostic_info(
        self, 
        reward_info: Dict[str, Any],
        expect_no_op: bool
    ) -> RenderableType:
        """Create diagnostic information panel."""
        info = reward_info.get('info', {})
        
        text = Text()
        text.append("Diagnostic Details\n", style="bold cyan")
        text.append("─" * 40 + "\n", style="dim")
        
        # Check type of diagnostic
        if 'r_actions' in info:
            # Database state check
            r_actions = info.get('r_actions', False)
            gt_hash = info.get('gt_data_hash', 'N/A')
            
            if r_actions:
                text.append("✓ ", style="green bold")
                text.append("Database state: ", style="white")
                text.append("CORRECT\n", style="green")
            else:
                text.append("✗ ", style="red bold")
                text.append("Database state: ", style="white")
                text.append("INCORRECT\n", style="red")
            
            text.append("  Expected hash: ", style="dim")
            text.append(f"{gt_hash[:16]}...\n", style="dim italic")
            
            if expect_no_op:
                text.append("\n")
                text.append("  Note: ", style="yellow bold")
                text.append("This task expected NO database modifications\n", style="yellow")
        
        elif 'r_outputs' in info:
            # Outputs check
            r_outputs = info.get('r_outputs', 0.0)
            
            if r_outputs >= 1.0:
                text.append("✓ ", style="green bold")
                text.append("All required outputs communicated\n", style="green")
            else:
                text.append("✗ ", style="red bold")
                text.append("Missing required outputs\n", style="red")
        
        return Panel(text, border_style="dim")


