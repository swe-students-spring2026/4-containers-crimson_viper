"""Pytest configuration for the web app test suite."""

import sys
from pathlib import Path


def add_web_app_to_path():
    """Add the web-app directory to sys.path for test imports."""
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
