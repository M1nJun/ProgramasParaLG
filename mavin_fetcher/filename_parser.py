from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ParsedImageName:
    cell_key: str            # derived from filename prefix
    region: str              # LOWER_B_L / LOWER_B_R / UPPER_B_L / UPPER_B_R
    map_type: str            # "SourceMap" or "ActiveMap"


def parse_image_filename(path: Path) -> Optional[ParsedImageName]:
    """
    Parse filenames like:
      l61SK02085_03-2_AN_083058_LOWER_2_B_L_..._SourceMap.jpg
      l61SK02085_03-2_AN_083058_UPPER_2_B_R_..._ActiveMap.jpg

    Robustness:
      - doesn't depend on the digit "2" (it can be missing or different)
      - extracts region using anchor tokens LOWER/UPPER + optional digit + B + L/R
      - cell_key is everything before LOWER/UPPER token
    """
    name = path.name
    lower = name.lower()
    if not (lower.endswith(".jpg") or lower.endswith(".jpeg") or lower.endswith(".png")):
        return None

    map_type: Optional[str] = None
    if "_sourcemap." in lower:
        map_type = "SourceMap"
    elif "_activemap." in lower:
        map_type = "ActiveMap"
    else:
        return None

    stem = path.stem  # drops extension
    parts = stem.split("_")

    # Find index of LOWER or UPPER
    idx = -1
    for i, p in enumerate(parts):
        if p == "LOWER" or p == "UPPER":
            idx = i
            break
    if idx < 0:
        return None

    # Extract region: (LOWER|UPPER) + optional digit + B + (L|R)
    # patterns:
    #   LOWER_2_B_L
    #   LOWER_B_L
    #   UPPER_3_B_R
    side = None
    # Expect 'B' and side within next 3 tokens
    # after LOWER/UPPER: could be digit, then B, then L/R
    j = idx + 1
    if j < len(parts) and parts[j].isdigit():
        j += 1

    if j < len(parts) and parts[j] == "B":
        if j + 1 < len(parts) and parts[j + 1] in ("L", "R"):
            side = parts[j + 1]
    else:
        # If format differs, attempt to find 'B' then side within next few parts
        # (keeps us resilient)
        window = parts[idx : min(len(parts), idx + 6)]
        for k in range(len(window) - 1):
            if window[k] == "B" and window[k + 1] in ("L", "R"):
                side = window[k + 1]
                break

    if side is None:
        return None

    region = f"{parts[idx]}_B_{side}"  # drop any digit entirely

    cell_key = "_".join(parts[:idx]).strip()
    if not cell_key:
        # last resort fallback: whole stem
        cell_key = stem

    return ParsedImageName(cell_key=cell_key, region=region, map_type=map_type)
