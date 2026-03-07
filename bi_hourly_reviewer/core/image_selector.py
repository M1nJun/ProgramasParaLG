"""
Image file selection.

Responsibilities:
    - Given a cell image folder and a defect side, select the correct
      image files by matching ending patterns.

Does NOT locate folders (image_locator) or copy files (image_fetcher).
"""

import os
from typing import List

from config import UPPER_IMAGE_PATTERNS, LOWER_IMAGE_PATTERNS
from core.defect_analyzer import SIDE_UPPER, SIDE_LOWER, SIDE_BOTH


def get_patterns_for_side(side: str) -> List[str]:
    """
    Return the file ending patterns to match for a given defect side.

    Args:
        side: "UPPER", "LOWER", or "BOTH".

    Returns:
        List of filename ending patterns.
    """
    if side == SIDE_UPPER:
        return list(UPPER_IMAGE_PATTERNS)
    elif side == SIDE_LOWER:
        return list(LOWER_IMAGE_PATTERNS)
    elif side == SIDE_BOTH:
        return list(UPPER_IMAGE_PATTERNS) + list(LOWER_IMAGE_PATTERNS)
    else:
        # UNKNOWN side — return all patterns as fallback
        return list(UPPER_IMAGE_PATTERNS) + list(LOWER_IMAGE_PATTERNS)


def select_images_from_folder(folder_path: str, side: str) -> List[str]:
    """
    Select image files from a cell folder based on the defect side.

    Matches files by their ending pattern (e.g. files ending in "_0_0.jpg").

    Args:
        folder_path: Full path to the cell's image folder.
        side: "UPPER", "LOWER", or "BOTH".

    Returns:
        List of full file paths to the selected images, sorted.
    """
    if not os.path.isdir(folder_path):
        return []

    patterns = get_patterns_for_side(side)
    all_files = os.listdir(folder_path)
    selected = []

    for pattern in patterns:
        for fname in all_files:
            if fname.lower().endswith(pattern.lower()):
                selected.append(os.path.join(folder_path, fname))
                break  # One match per pattern

    return sorted(selected)


def categorize_images(image_paths: List[str]) -> dict:
    """
    Categorize selected images into originals and overlays for display.

    Returns:
        Dict with keys:
            "originals": list of non-overlay image paths
            "overlays": list of overlay image paths
            "pairs": list of (original, overlay) tuples where available
    """
    originals = [p for p in image_paths if "_overlay" not in os.path.basename(p).lower()]
    overlays = [p for p in image_paths if "_overlay" in os.path.basename(p).lower()]

    # Pair them: an overlay's base name is the original name + "_overlay"
    pairs = []
    for orig in originals:
        orig_base = os.path.splitext(os.path.basename(orig))[0]
        expected_overlay = orig_base + "_overlay"
        matching = [
            ov for ov in overlays
            if os.path.splitext(os.path.basename(ov))[0].lower() == expected_overlay.lower()
        ]
        overlay = matching[0] if matching else None
        pairs.append((orig, overlay))

    return {
        "originals": originals,
        "overlays": overlays,
        "pairs": pairs,
    }