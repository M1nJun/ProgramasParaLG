"""
DL Crop image file selection.

Responsibilities:
    - Given a crop folder (with or without class subfolders), find the
      image files matching a specific cell_id + side + defect tokens.
    - Return matched file paths.

Matching logic:
    A filename matches if it contains ALL of:
        - The cell_id (e.g. "a635K06000")
        - The side (e.g. "UPPER" or "LOWER")
        - All match_tokens (e.g. ["A_L"] or ["HORN MARK LEFT"])
"""

import os
from typing import List


def match_crop_images_in_folder(
    folder_path: str,
    cell_id: str,
    side: str,
    match_tokens: List[str],
) -> List[str]:
    """
    Find crop images in a single folder matching cell_id + side + tokens.

    Args:
        folder_path: Directory to search.
        cell_id: Cell ID to match in filename.
        side: "UPPER" or "LOWER".
        match_tokens: List of strings that must all appear in the filename.

    Returns:
        List of matching file paths, sorted.
    """
    if not os.path.isdir(folder_path):
        return []

    matched = []
    for fname in os.listdir(folder_path):
        if not os.path.isfile(os.path.join(folder_path, fname)):
            continue
        if _filename_matches(fname, cell_id, side, match_tokens):
            matched.append(os.path.join(folder_path, fname))

    return sorted(matched)


def match_crop_images_in_subfolders(
    parent_folder: str,
    cell_id: str,
    side: str,
    match_tokens: List[str],
) -> List[str]:
    """
    Find crop images across all class subfolders within a crop folder.
    Used for crop types with class subfolders (Crop_A, Crop_B).

    Args:
        parent_folder: The crop folder containing class subfolders.
        cell_id: Cell ID to match.
        side: "UPPER" or "LOWER".
        match_tokens: Tokens to match in filename.

    Returns:
        List of matching file paths from any subfolder, sorted.
    """
    if not os.path.isdir(parent_folder):
        return []

    matched = []
    for entry in os.listdir(parent_folder):
        subfolder = os.path.join(parent_folder, entry)
        if os.path.isdir(subfolder):
            matched.extend(
                match_crop_images_in_folder(subfolder, cell_id, side, match_tokens)
            )

    return sorted(matched)


def select_crop_images(
    crop_folder_path: str,
    has_subfolders: bool,
    cell_id: str,
    side: str,
    match_tokens: List[str],
) -> List[str]:
    """
    High-level selector: find crop images using the right search strategy.

    Args:
        crop_folder_path: Path to the crop folder.
        has_subfolders: True if images are inside class subfolders.
        cell_id: Cell ID to match.
        side: "UPPER" or "LOWER".
        match_tokens: Tokens to match in filename.

    Returns:
        List of matching file paths.
    """
    if has_subfolders:
        return match_crop_images_in_subfolders(
            crop_folder_path, cell_id, side, match_tokens
        )
    else:
        return match_crop_images_in_folder(
            crop_folder_path, cell_id, side, match_tokens
        )


def _filename_matches(
    filename: str,
    cell_id: str,
    side: str,
    match_tokens: List[str],
) -> bool:
    """
    Check if a filename contains cell_id, side, and all match tokens.
    """
    if cell_id not in filename:
        return False
    if side not in filename:
        return False
    for token in match_tokens:
        if token not in filename:
            return False
    return True