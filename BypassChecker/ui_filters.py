from __future__ import annotations

from typing import List

from checker import MeasureRow


def filter_rows(rows: List[MeasureRow], mode: str, query: str) -> List[MeasureRow]:
    """
    mode:
      - "All"
      - "Fail"
      - "Pass"
      - "Missing"
      - "Bypassed"
    """
    q = (query or "").strip().lower()

    def matches_query(r: MeasureRow) -> bool:
        if not q:
            return True
        return (q in r.display_name.lower()) or (q in r.normalized_key.lower())

    def matches_mode(r: MeasureRow) -> bool:
        if mode == "Fail":
            return not r.is_pass
        if mode == "Pass":
            return r.is_pass
        if mode == "Missing":
            return r.is_missing
        if mode == "Bypassed":
            return r.has_bypassed
        return True

    return [r for r in rows if matches_mode(r) and matches_query(r)]
