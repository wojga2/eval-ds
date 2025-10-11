"""
Bee Sample Viewer - Interactive TUI for viewing bee run samples.

A terminal user interface for browsing and analyzing samples from bee runs,
with full agentic trajectories, metrics, and debug information.
"""

from .app import BeeViewerApp
from .widgets import JSONViewer, SampleDetail, SampleList

__version__ = "0.1.0"
__all__ = ["BeeViewerApp", "JSONViewer", "SampleDetail", "SampleList"]



