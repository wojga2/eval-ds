"""
Main application for Bee Sample Viewer.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, TabbedContent, TabPane, Label, Rule
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding

from .widgets import JSONViewer, SampleDetail, SampleList
from .reward_explanation import RewardExplanationViewer


class BeeViewerApp(App):
    """Interactive TUI for viewing bee run samples."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #sidebar {
        width: 40;
        background: $panel;
        border-right: solid $primary;
    }
    
    #main {
        background: $surface;
    }
    
    #sample-list {
        height: 1fr;
    }
    
    #detail-panel {
        height: 1fr;
    }
    
    .stats-bar {
        height: 3;
        background: $panel;
        padding: 1;
        border-bottom: solid $primary;
    }
    
    .status-header {
        height: auto;
        padding: 0 1;
        background: $panel;
    }
    
    DataTable {
        height: 100%;
    }
    
    TabbedContent {
        height: 100%;
    }
    
    TabPane {
        padding: 0;
    }
    
    SampleDetail {
        height: auto;
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("j", "next_sample", "Next", show=False),
        Binding("k", "prev_sample", "Previous", show=False),
        Binding("left", "prev_sample", "Previous"),
        Binding("right", "next_sample", "Next"),
        Binding("down", "scroll_down", "Scroll Down", show=False),
        Binding("up", "scroll_up", "Scroll Up", show=False),
        Binding("shift+down", "page_down", "Page Down", show=False),
        Binding("shift+up", "page_up", "Page Up", show=False),
        Binding("m", "toggle_markdown", "Markdown", priority=True),
        Binding("home", "scroll_home", "Top", show=False),
        Binding("end", "scroll_end", "Bottom", show=False),
        Binding("?", "toggle_help", "Help"),
    ]
    
    TITLE = "🐝 Bee Sample Viewer"
    
    def __init__(self, jsonl_file: Optional[str] = None):
        super().__init__()
        self.jsonl_file = jsonl_file
        self.samples: List[Dict[str, Any]] = []
        self.filtered_samples: List[Dict[str, Any]] = []
        self.current_sample_index = 0
    
    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header()
        
        with Horizontal():
            # Left sidebar: Sample list
            with Vertical(id="sidebar"):
                with Container(classes="stats-bar"):
                    yield Label("Samples: 0", id="stats-label")
                
                yield SampleList(id="sample-list")
            
            # Main panel: Sample details
            with Vertical(id="main"):
                yield SampleDetail(id="sample-summary")
                yield Label("", id="status-header", classes="status-header")
                yield Rule()
                
                with TabbedContent(id="detail-panel"):
                    with TabPane("Reward Explanation", id="tab-reward"):
                        yield RewardExplanationViewer(id="reward-explanation")
                    
                    with TabPane("Outputs", id="tab-outputs"):
                        yield JSONViewer(id="json-outputs")
                    
                    with TabPane("Inputs", id="tab-inputs"):
                        yield JSONViewer(id="json-inputs")
                    
                    with TabPane("Metrics", id="tab-metrics"):
                        yield JSONViewer(id="json-metrics")
                    
                    with TabPane("Debug Info", id="tab-debug"):
                        yield JSONViewer(id="json-debug")
                    
                    with TabPane("Full Sample", id="tab-full"):
                        yield JSONViewer(id="json-full")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Load data when app starts."""
        # Set up the sample list table
        table = self.query_one("#sample-list", SampleList)
        table.add_columns("ID", "Task", "Pass")
        
        # Load file if provided
        if self.jsonl_file:
            self.load_jsonl_file(self.jsonl_file)
        else:
            # Try to find the most recent JSONL file in output directory
            self.auto_load_latest_file()
    
    def auto_load_latest_file(self) -> None:
        """Find and load the most recent JSONL file."""
        output_dir = Path("output")
        if not output_dir.exists():
            self.notify("No output directory found. Use 'download-bee-run' first.", severity="warning")
            return
        
        jsonl_files = sorted(output_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if jsonl_files:
            self.load_jsonl_file(str(jsonl_files[0]))
        else:
            self.notify("No JSONL files found in output directory.", severity="warning")
    
    def load_jsonl_file(self, filepath: str) -> None:
        """Load samples from a JSONL file."""
        try:
            path = Path(filepath)
            self.samples = []
            
            with open(path, 'r') as f:
                for line in f:
                    if line.strip():
                        self.samples.append(json.loads(line))
            
            self.filtered_samples = self.samples.copy()
            self.update_sample_list()
            self.update_stats()
            
            # Select first sample
            if self.samples:
                self.current_sample_index = 0
                self.show_sample(0)
                
                # Highlight first row
                table = self.query_one("#sample-list", SampleList)
                table.move_cursor(row=0)
            
            self.notify(f"Loaded {len(self.samples)} samples from {path.name}", severity="information")
            
        except Exception as e:
            self.notify(f"Error loading file: {e}", severity="error")
    
    def update_sample_list(self) -> None:
        """Update the sample list table."""
        table = self.query_one("#sample-list", SampleList)
        table.clear()
        
        for i, sample in enumerate(self.filtered_samples):
            # Extract key information
            sample_id = str(sample.get("sample_id", ""))[:8]
            task_name = sample.get("task_name", "")[:20]
            
            # Get pass/fail metric
            metrics = sample.get("metrics", {})
            pass_val = metrics.get("passed", metrics.get("pass", metrics.get("pass@01", "")))
            pass_str = "✓" if pass_val == 1.0 else "✗" if pass_val == 0.0 else str(pass_val)
            
            table.add_row(sample_id, task_name, pass_str)
    
    def update_stats(self) -> None:
        """Update the stats label."""
        stats_label = self.query_one("#stats-label", Label)
        stats_label.update(f"Samples: {len(self.filtered_samples)} / {len(self.samples)}")
    
    def show_sample(self, index: int) -> None:
        """Display details of a specific sample."""
        if 0 <= index < len(self.filtered_samples):
            sample = self.filtered_samples[index]
            self.current_sample_index = index
            
            # Update summary
            try:
                summary = self.query_one("#sample-summary", SampleDetail)
                summary.sample = sample
            except Exception as e:
                self.log(f"Error updating summary: {e}")
            
            # Update status header
            self._update_status_header(sample, index)
            
            # Update all viewers
            try:
                self.query_one("#reward-explanation", RewardExplanationViewer).data = sample
                self.query_one("#json-outputs", JSONViewer).data = sample.get("outputs")
                self.query_one("#json-inputs", JSONViewer).data = sample.get("inputs")
                self.query_one("#json-metrics", JSONViewer).data = sample.get("metrics")
                self.query_one("#json-debug", JSONViewer).data = sample.get("debug_info")
                self.query_one("#json-full", JSONViewer).data = sample
            except Exception as e:
                self.log(f"Error updating viewers: {e}")
                self.notify(f"Display error: {e}", severity="error")
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the sample list."""
        self.show_sample(event.cursor_row)
    
    def action_next_sample(self) -> None:
        """Move to next sample."""
        if self.current_sample_index < len(self.filtered_samples) - 1:
            new_index = self.current_sample_index + 1
            self.show_sample(new_index)
            table = self.query_one("#sample-list", SampleList)
            table.move_cursor(row=new_index)
    
    def action_prev_sample(self) -> None:
        """Move to previous sample."""
        if self.current_sample_index > 0:
            new_index = self.current_sample_index - 1
            self.show_sample(new_index)
            table = self.query_one("#sample-list", SampleList)
            table.move_cursor(row=new_index)
    
    def _get_active_viewer(self) -> Optional[JSONViewer]:
        """Get the JSONViewer for the currently active tab."""
        try:
            tabbed = self.query_one(TabbedContent)
            active_pane_id = tabbed.active
            
            tab_to_viewer = {
                "tab-reward": None,  # Reward explanation is not a JSONViewer
                "tab-outputs": "json-outputs",
                "tab-inputs": "json-inputs",
                "tab-metrics": "json-metrics",
                "tab-debug": "json-debug",
                "tab-full": "json-full",
            }
            
            viewer_id = tab_to_viewer.get(active_pane_id)
            if viewer_id:
                return self.query_one(f"#{viewer_id}", JSONViewer)
        except Exception as e:
            self.log(f"Error getting active viewer: {e}")
        return None
    
    def _update_status_header(self, sample: Dict[str, Any], index: int) -> None:
        """Update the status header with color-coded pass/fail info."""
        from rich.text import Text
        
        try:
            status_header = self.query_one("#status-header", Label)
        except:
            return  # Header not found, skip
        
        # Extract metrics
        metrics = sample.get("metrics", {})
        reward = metrics.get("mean_reward")
        expect_no_op = metrics.get("expect_no_op", False)
        
        # Get task info for context
        task_run_info = sample.get("task_run_info", {})
        task_name = task_run_info.get("task_name", "Unknown")
        task_metrics = task_run_info.get("task_metrics", {})
        
        # Extract task success rate if available
        task_success_rate = None
        for key in task_metrics:
            if "mean_reward" in key and "/" in key:
                task_success_rate = task_metrics[key]
                break
        
        # Build status text with colors
        text = Text()
        
        # Sample number
        text.append(f"Sample #{index + 1}/{len(self.filtered_samples)}", style="bold white")
        text.append(" | ", style="dim white")
        
        # Pass/Fail status with color-coding
        if reward is not None:
            if reward >= 1.0:
                text.append("✅ PASSED", style="bold green")
            elif reward > 0.0:
                text.append("⚠️  PARTIAL", style="bold yellow")
            else:
                text.append("❌ FAILED", style="bold red")
            text.append(f" (Reward: {reward:.1f})", style="dim white")
        else:
            text.append("⚪ NO REWARD", style="dim white")
        
        text.append(" | ", style="dim white")
        
        # Task name (abbreviated)
        task_short = task_name.split(".")[-1] if "." in task_name else task_name
        text.append(f"Task: {task_short}", style="cyan")
        
        # Task success rate if available
        if task_success_rate is not None:
            text.append(f" ({task_success_rate:.1%} overall)", style="dim cyan")
        
        text.append(" | ", style="dim white")
        
        # No-op status
        if expect_no_op:
            text.append("No-Op: True", style="yellow")
        else:
            text.append("No-Op: False", style="dim white")
        
        status_header.update(text)
    
    def action_scroll_up(self) -> None:
        """Scroll current content up by one line."""
        try:
            viewer = self._get_active_viewer()
            if viewer:
                viewer.scroll_up()
        except Exception as e:
            self.log(f"Error scrolling: {e}")
    
    def action_scroll_down(self) -> None:
        """Scroll current content down by one line."""
        try:
            viewer = self._get_active_viewer()
            if viewer:
                viewer.scroll_down()
        except Exception as e:
            self.log(f"Error scrolling: {e}")
    
    def action_page_down(self) -> None:
        """Scroll current content down by one page."""
        try:
            viewer = self._get_active_viewer()
            if viewer:
                viewer.scroll_page_down()
        except Exception as e:
            self.log(f"Error scrolling: {e}")
    
    def action_page_up(self) -> None:
        """Scroll current content up by one page."""
        try:
            viewer = self._get_active_viewer()
            if viewer:
                viewer.scroll_page_up()
        except Exception as e:
            self.log(f"Error scrolling: {e}")
    
    def action_scroll_home(self) -> None:
        """Scroll to top of content."""
        try:
            viewer = self._get_active_viewer()
            if viewer:
                viewer.scroll_home()
        except Exception as e:
            self.log(f"Error scrolling: {e}")
    
    def action_scroll_end(self) -> None:
        """Scroll to bottom of content."""
        try:
            viewer = self._get_active_viewer()
            if viewer:
                viewer.scroll_end()
        except Exception as e:
            self.log(f"Error scrolling: {e}")
    
    def action_toggle_markdown(self) -> None:
        """Toggle markdown mode for the active tab's content viewer."""
        try:
            # Get the active tab's JSONViewer
            tabbed = self.query_one(TabbedContent)
            active_pane_id = tabbed.active
            
            # Map tab IDs to viewer IDs
            tab_to_viewer = {
                "tab-reward": None,  # Reward explanation doesn't support markdown toggle
                "tab-outputs": "json-outputs",
                "tab-inputs": "json-inputs",
                "tab-metrics": "json-metrics",
                "tab-debug": "json-debug",
                "tab-full": "json-full",
            }
            
            viewer_id = tab_to_viewer.get(active_pane_id)
            if viewer_id:
                viewer = self.query_one(f"#{viewer_id}", JSONViewer)
                viewer.action_toggle_markdown()
            elif active_pane_id == "tab-reward":
                # Reward explanation doesn't support markdown toggle
                pass
            else:
                self.log(f"Unknown active pane: {active_pane_id}")
        except Exception as e:
            self.log(f"Error toggling markdown: {e}")
    
    def action_toggle_help(self) -> None:
        """Show help information."""
        help_text = """
🐝 Bee Sample Viewer - Keyboard Shortcuts

📋 Sample Navigation:
  ←/→            Previous/Next sample
  j/k            Previous/Next sample (vim-style)
  Tab            Switch between tabs (Outputs/Inputs/Metrics/etc)
  
📜 Content Scrolling (works automatically on active tab):
  ↑/↓            Scroll content line by line
  Shift+↑/↓      Scroll content page by page
  Home           Jump to top of content
  End            Jump to bottom of content
  
🎨 Viewing:
  m              Toggle Markdown mode (formats text beautifully!)
  
⚡ General:
  q              Quit
  ?              This help
  
💡 Workflow:
  1. Use ←/→ or j/k to browse samples
  2. Press Tab to switch tabs (Outputs, Metrics, etc)
  3. Press 'm' to toggle Markdown view (great for raw_prompt!)
  4. Use ↑/↓ to scroll, Shift+↑/↓ for faster paging
  5. All scrolling works automatically - no focus needed!
  
🎨 Markdown Mode:
  - Renders headers, lists, bold/italic text
  - Extracts and formats JSON code blocks
  - Syntax highlights with line numbers
  - Pretty-prints JSON with proper indentation
        """
        self.notify(help_text, title="Help", timeout=25)

