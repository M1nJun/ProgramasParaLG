"""
DL Crop image fetching (cache-backed).

Responsibilities:
    - Given a defect record and a pre-built CropCache, look up and
      copy the matching crop images to the output directory.
    - Handle single configs and multi-config defects (e.g. B_DIM_L
      triggers both HORNMARK and LEADEDGE).

Uses CropCache for O(1) lookups instead of scanning directories per cell.
"""

import shutil
import os
from typing import Dict, List

from config import CROP_DEFECT_MAP
from core.crop_cache import CropCache


def get_crop_configs(judge_defect: str) -> List[Dict]:
    """
    Look up the crop configuration(s) for a JUDGE-DEFECT value.

    Returns a list of config dicts. Most defects return a single config,
    but some (like B_DIM_L) return multiple.

    Returns:
        List of crop config dicts, or empty list if no crop applies.
    """
    entry = CROP_DEFECT_MAP.get(judge_defect)
    if entry is None:
        return []
    if isinstance(entry, list):
        return entry
    return [entry]


def fetch_crops_for_cell(
    defect_record: Dict,
    output_dir: str,
    cache: CropCache,
) -> Dict:
    """
    Fetch crop images for a single cell using the pre-built cache.

    Args:
        defect_record: Dict from defect_analyzer.build_defect_record().
        output_dir: The cell's output directory (same as main images).
        cache: Pre-built CropCache instance.

    Returns:
        Dict with results:
            crop_files_copied: total count of crop files copied
            crop_details: list of per-config result dicts
            crop_errors: list of error strings
    """
    judge_defect = defect_record["judge_defect"]
    cell_id = defect_record["cell_id"]
    detected_side = defect_record["side"]

    configs = get_crop_configs(judge_defect)
    if not configs:
        return {"crop_files_copied": 0, "crop_details": [], "crop_errors": []}

    details = []
    errors = []
    total_copied = 0

    for cfg in configs:
        result = _fetch_single_crop_config(
            cfg, cell_id, detected_side, output_dir, cache
        )
        if result["error"]:
            errors.append(result["error"])
        else:
            total_copied += result["copied_count"]
        details.append(result)

    return {
        "crop_files_copied": total_copied,
        "crop_details": details,
        "crop_errors": errors,
    }


def _fetch_single_crop_config(
    cfg: Dict,
    cell_id: str,
    detected_side: str,
    output_dir: str,
    cache: CropCache,
) -> Dict:
    """
    Fetch crop images for a single crop configuration using cached lookup.
    """
    crop_folder = cfg["crop_folder"]
    match_tokens = cfg["match_tokens"]
    side_override = cfg.get("side_override")

    # Check if this folder was found during indexing
    if not cache.is_folder_available(crop_folder):
        return {
            "crop_folder": crop_folder,
            "side": side_override or detected_side,
            "copied_count": 0,
            "copied_files": [],
            "error": f"Crop folder '{crop_folder}' not found on any drive",
        }

    # Determine which side(s) to search for
    side = side_override if side_override else detected_side
    sides_to_search = _resolve_sides(side)

    # Lookup and copy for each side
    all_copied = []
    for search_side in sides_to_search:
        matched = cache.lookup(cell_id, search_side, crop_folder, match_tokens)
        for src in matched:
            if os.path.isfile(src):
                os.makedirs(output_dir, exist_ok=True)
                dst = os.path.join(output_dir, os.path.basename(src))
                shutil.copy2(src, dst)
                all_copied.append(dst)

    return {
        "crop_folder": crop_folder,
        "side": side,
        "copied_count": len(all_copied),
        "copied_files": all_copied,
        "error": None,
    }


def _resolve_sides(side: str) -> List[str]:
    """
    Convert a side value into a list of sides to search.
    "BOTH" becomes ["UPPER", "LOWER"].
    """
    if side == "BOTH":
        return ["UPPER", "LOWER"]
    return [side]