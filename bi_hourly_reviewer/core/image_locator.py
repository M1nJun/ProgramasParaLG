"""
Image folder location.

Responsibilities:
    - Build the expected directory path from defect record fields.
    - Scan available drives to find the correct image folder.
    - Search for the cell-specific subfolder by CELL-ID suffix.

Does NOT copy files — that is handled by image_fetcher.py.
"""

import os
from typing import Optional, List

from config import (
    IMAGE_BASE_SUBPATH,
    IMAGE_JUDGE_SUBDIRS,
    get_available_drives,
)


def build_image_base_path(drive: str, model_id: str, date_str: str, hour: int) -> str:
    """
    Build the base image directory path for a given drive, model, date, and hour.

    Example result:
        F:\\Files\\Image\\JF2\\2026\\02\\28\\00

    Args:
        drive: Drive letter (e.g. "F").
        model_id: Model name (e.g. "JF2").
        date_str: Date in YYYYMMDD format.
        hour: Hour as integer (0-23).

    Returns:
        Full directory path string.
    """
    yyyy = date_str[0:4]
    mm = date_str[4:6]
    dd = date_str[6:8]
    hh = f"{hour:02d}"

    return os.path.join(f"{drive}:\\", IMAGE_BASE_SUBPATH, model_id, yyyy, mm, dd, hh)


def get_judge_subdir(judge: str) -> str:
    """
    Get the subdirectory name for a given JUDGE value.

    NG     -> "NG"
    DLNG   -> "OK\\DL_CANDIDATE"
    C-NG   -> "OK\\DL_CANDIDATE"
    """
    return IMAGE_JUDGE_SUBDIRS.get(judge, "NG")


def build_search_dir(drive: str, model_id: str, date_str: str, hour: int, judge: str) -> str:
    """
    Build the full search directory where cell folders should be located.

    Example:
        F:\\Files\\Image\\JF2\\2026\\02\\28\\00\\NG
        F:\\Files\\Image\\JF2\\2026\\02\\28\\00\\OK\\DL_CANDIDATE
    """
    base = build_image_base_path(drive, model_id, date_str, hour)
    judge_subdir = get_judge_subdir(judge)
    return os.path.join(base, judge_subdir)


def find_cell_folder(search_dir: str, cell_id: str) -> Optional[str]:
    """
    Search for a folder ending with _<cell_id> within the search directory.

    Args:
        search_dir: Directory to search in.
        cell_id: Cell ID to match (e.g. "j62SK05777").

    Returns:
        Full path to the cell folder, or None if not found.
    """
    if not os.path.isdir(search_dir):
        return None

    suffix = f"_{cell_id}"
    for entry in os.listdir(search_dir):
        full_path = os.path.join(search_dir, entry)
        if os.path.isdir(full_path) and entry.endswith(suffix):
            return full_path

    return None


def locate_cell_images_across_drives(
    model_id: str,
    date_str: str,
    hour: int,
    judge: str,
    cell_id: str,
    drives: List[str] = None,
) -> Optional[str]:
    """
    Scan all available drives to find the image folder for a specific cell.

    Args:
        model_id: Model name (e.g. "JF2").
        date_str: Date in YYYYMMDD format.
        hour: Hour as integer.
        judge: JUDGE value ("NG", "DLNG", "C-NG").
        cell_id: Cell ID to search for.
        drives: Optional list of drive letters to search. Defaults to auto-detect.

    Returns:
        Full path to the cell's image folder, or None if not found on any drive.
    """
    drive_list = drives or get_available_drives()

    for drive in drive_list:
        search_dir = build_search_dir(drive, model_id, date_str, hour, judge)
        cell_folder = find_cell_folder(search_dir, cell_id)
        if cell_folder is not None:
            return cell_folder

    return None