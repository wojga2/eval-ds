"""
Entry point for the Bee Sample Viewer application.
"""

import argparse
from .app import BeeViewerApp


def main():
    """Entry point for the TUI viewer."""
    parser = argparse.ArgumentParser(
        description="Interactive TUI viewer for bee run samples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View most recent download
  uv run view-bee-samples
  
  # View specific file
  uv run view-bee-samples output/task_GSM8k_*.jsonl
  
  # View specific file with path
  uv run view-bee-samples /path/to/samples.jsonl

Keyboard Shortcuts:
  ↑/↓ or j/k  Navigate samples
  Tab         Switch tabs
  Space       Focus content for scrolling
  q           Quit
  ?           Help
        """
    )
    
    parser.add_argument(
        "file",
        nargs="?",
        help="JSONL file to view (defaults to most recent in output/)"
    )
    
    args = parser.parse_args()
    
    # Run the app
    app = BeeViewerApp(jsonl_file=args.file)
    app.run()


if __name__ == "__main__":
    main()



