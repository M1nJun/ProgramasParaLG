from __future__ import annotations

import re
from typing import Iterable, List, Tuple


_NORMALIZE_RE = re.compile(r"[_\s]+")


def normalize_measure_name(name: str) -> str:
    """
    Normalization rule (per your spec):
      - lowercase
      - remove underscores and whitespace
    Example:
      'LONG_TAPE_L' -> 'longtapel'
      'Long Tape L' -> 'longtapel'
    """
    if name is None:
        return ""
    s = name.strip().lower()
    s = _NORMALIZE_RE.sub("", s)
    return s


def dedupe_preserve_order(names: Iterable[str]) -> Tuple[List[str], List[str]]:
    """
    Dedupe a list (within a single column) after normalization, while preserving
    first-seen order.

    Returns:
      (deduped_original_names, duplicates_original_names)

    NOTE:
      - This does NOT dedupe across Upper/Lower; the caller controls scope.
      - Duplicates are detected by normalized key, but we return the original strings.
    """
    seen = set()
    out: List[str] = []
    dups: List[str] = []

    for raw in names:
        if raw is None:
            continue
        r = str(raw).strip()
        if not r:
            continue
        key = normalize_measure_name(r)
        if not key:
            continue

        if key in seen:
            dups.append(r)
            continue

        seen.add(key)
        out.append(r)

    return out, dups
