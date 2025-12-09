"""
analyze_text.py (root-level wrapper)

Allows you to run analysis via:

    python analyze_text.py "some Sanskrit text"

This simply calls `src.analyze_text.analyze_verse`.
"""

from __future__ import annotations

import sys

from src.analyze_text import analyze_verse


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_text.py '<Sanskrit text>'")
        raise SystemExit(1)

    text = sys.argv[1]
    analyze_verse(text)
