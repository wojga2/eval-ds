#!/usr/bin/env python3
"""
Wrapper to run bee experiments from eval-ds repo.
This allows running bee without requiring the apiary checkout.
"""
import sys
import subprocess


def main():
    """Run bee with all arguments passed through."""
    # Simply invoke bee as a module
    args = ["python", "-m", "bee"] + sys.argv[1:]
    sys.exit(subprocess.call(args))


if __name__ == "__main__":
    main()

