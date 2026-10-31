#!/usr/bin/env python3
"""Compatibility entry point for the standalone Raspberry Wi-Fi panel."""
import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).resolve().parent / "raspberry" / "touchscreen" / "cuty_wifi_panel.py"),
        run_name="__main__",
    )
