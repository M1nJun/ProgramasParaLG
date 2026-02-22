from __future__ import annotations

from dataclasses import dataclass

TARGET_DEFECTS: set[str] = {
    "B_DIM_L",
    "B_DIM_R",
    "H_DIM_L",
    "H_DIM_R",
}

def normalize_defect(value: str) -> str:
    return (value or "").strip().upper()

def is_target_defect(value: str) -> bool:
    return normalize_defect(value) in TARGET_DEFECTS

def side_from_defect(value: str) -> str:
    """Return "L" or "R" from a defect like B_DIM_L."""
    d = normalize_defect(value)
    if d.endswith("_L"):
        return "L"
    if d.endswith("_R"):
        return "R"
    raise ValueError(f"Cannot derive side from defect: {value!r}")

@dataclass(frozen=True)
class DefectHit:
    defect: str  # e.g. B_DIM_L
    side: str    # L or R
    cell_id: str
    upper_img_path: str
    upper_overlay_path: str