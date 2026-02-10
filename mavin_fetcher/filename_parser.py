from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ParsedImageName:
    cell_key: str            # derived from filename prefix
    region: str              # LOWER_A_L / LOWER_A_R / UPPER_A_L / UPPER_A_R (or B)
    map_type: str            # "SourceMap" or "ActiveMap"
    polarity: str            # "ANODE" or "CATHODE"


def _detect_map_type(lower_name: str) -> Optional[str]:
    if "_sourcemap." in lower_name:
        return "SourceMap"
    if "_activemap." in lower_name:
        return "ActiveMap"
    return None


def _detect_polarity(parts: list[str]) -> Optional[str]:
    # Your guaranteed tokens:
    #   ... _AN_ ...  -> ANODE
    #   ... _CA_ ...  -> CATHODE
    # Example:
    #   b61RK02140_03-2_AN_142953_UPPER_1_A_L_..._SourceMap.jpg
    #   b61RK02140_04-1_CA_142953_UPPER_1_A_L_..._SourceMap.jpg
    for p in parts:
        if p == "AN":
            return "ANODE"
        if p == "CA":
            return "CATHODE"
    return None


def parse_image_filename(path: Path) -> Optional[ParsedImageName]:
    """
    Parse filenames like:
      c61RK02525_03-2_AN_142845_UPPER_1_A_L_..._SourceMap.jpg
      b61RK02140_04-1_CA_142953_UPPER_1_A_L_..._ActiveMap.jpg

    Robustness:
      - extracts region using anchor tokens LOWER/UPPER + optional digit + (A|B) + (L|R)
      - polarity uses exact token AN/CA (guaranteed by your rule)
      - cell_key is everything before LOWER/UPPER token
    """
    name = path.name
    lower = name.lower()
    if not (lower.endswith(".jpg") or lower.endswith(".jpeg") or lower.endswith(".png")):
        return None

    map_type = _detect_map_type(lower)
    if not map_type:
        return None

    stem = path.stem
    parts = stem.split("_")

    pol = _detect_polarity(parts)
    if not pol:
        return None

    # Find index of LOWER or UPPER
    idx = -1
    for i, p in enumerate(parts):
        if p == "LOWER" or p == "UPPER":
            idx = i
            break
    if idx < 0:
        return None

    # Extract: (LOWER|UPPER) + optional digit + (A|B) + (L|R)
    j = idx + 1
    if j < len(parts) and parts[j].isdigit():
        j += 1

    area_id: Optional[str] = None
    side: Optional[str] = None

    if j < len(parts) and parts[j] in ("A", "B"):
        area_id = parts[j]
        if j + 1 < len(parts) and parts[j + 1] in ("L", "R"):
            side = parts[j + 1]
    else:
        # fallback window scan
        window = parts[idx: min(len(parts), idx + 7)]
        for k in range(len(window) - 1):
            if window[k] in ("A", "B") and window[k + 1] in ("L", "R"):
                area_id = window[k]
                side = window[k + 1]
                break

    if area_id is None or side is None:
        return None

    region = f"{parts[idx]}_{area_id}_{side}"  # LOWER_A_L, UPPER_B_R, etc.
    cell_key = "_".join(parts[:idx]).strip() or stem

    return ParsedImageName(cell_key=cell_key, region=region, map_type=map_type, polarity=pol)