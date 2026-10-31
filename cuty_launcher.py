#!/usr/bin/env python3
"""Compatibility entry point for the Raspberry touchscreen application."""
import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    touchscreen = Path(__file__).resolve().parent / "raspberry" / "touchscreen"
    sys.path.insert(0, str(touchscreen))
    runpy.run_path(str(touchscreen / "cuty_launcher.py"), run_name="__main__")
