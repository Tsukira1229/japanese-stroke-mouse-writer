# -*- coding: utf-8 -*-
"""Compatibility entry point for promoting the formal three-font style packs."""

from __future__ import annotations

try:
    from scripts.promote_full_three_font_style_packs import main
except ModuleNotFoundError:  # Direct `python scripts/generate_font_style_packs.py` execution.
    from promote_full_three_font_style_packs import main


if __name__ == "__main__":
    raise SystemExit(main())
