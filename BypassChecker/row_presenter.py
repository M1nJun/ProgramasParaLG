from __future__ import annotations

from typing import List

from checker import MeasureRow


def occurrences_text(row: MeasureRow, show_all: bool) -> str:
    """
    Compact by default:
      - If FAIL due to bypass: show only bypassed occurrences
      - If FAIL due to missing: show "(no occurrences found)" (and any partial occurrences)
      - If PASS: show first occurrence only (unless show_all)
    """
    if not row.occurrences:
        return "(no occurrences found)"

    def fmt(occ):
        return f"{occ.item_tag} | {occ.name} | bypass={str(occ.bypass).lower()}"

    if show_all:
        return "\n".join(fmt(o) for o in row.occurrences)

    # Compact mode:
    if row.has_bypassed:
        return "\n".join(fmt(o) for o in row.bypassed_occurrences)

    if row.is_missing:
        # show whatever exists (partial) but not too noisy
        return "\n".join(fmt(o) for o in row.occurrences[:2]) + ("\n..." if len(row.occurrences) > 2 else "")

    # PASS
    return fmt(row.occurrences[0])
