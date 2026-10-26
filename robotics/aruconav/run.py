#!/usr/bin/env python3
"""Convenience launcher for ArUcoNav from project root."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from aruconav.main import main

if __name__ == "__main__":
    main()
