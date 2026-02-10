from __future__ import annotations

from typing import Set


def _norm(name: str) -> str:
    return (name or "").strip().lower()


def excluded_class_folders_for_area(area_id: str) -> Set[str]:
    """
    Returns lowercase folder names to exclude from scan/copy.
    """
    a = (area_id or "").strip().upper()

    # Existing B-area exclusions (already in config.py):
    base = {
        _norm("01_ok_anode"),
        _norm("01_ok_cathode"),
    }

    if a == "A":
        base |= {
            _norm("01_OK_TOP_ANODE"),
            _norm("02_OK_BACK_ANODE"),
            _norm("01_OK_TOP_CATHODE"),
            _norm("02_OK_BACK_CATHODE"),
        }

    return base