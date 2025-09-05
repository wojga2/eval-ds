#!/usr/bin/env python3
"""
eval-ds: Simple library for loading and analyzing bee run samples.

This package provides tools for:
1. Connecting to the BeeDB database
2. Loading samples from specific bee runs or task runs
3. Converting samples to pandas DataFrame for analysis
4. Basic data exploration and statistics
"""

__version__ = "0.1.0"

from .main import BeeRunLoader

__all__ = ["BeeRunLoader"]
