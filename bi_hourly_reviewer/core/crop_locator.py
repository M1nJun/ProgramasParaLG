"""
DL Crop image folder location.

Responsibilities:
    - Build the Mavin crop directory path for a given date and model.
    - Scan drives to find the correct Mavin folder.
    - List class subfolders within a crop folder.

Path structure (day level, no hour):
    <Drive>:\\Files\\Image\\<MODEL>\\<YYYY>\\<MM>\\<DD>\\Mavin\\<crop_folder>\\...
"""

import os
from typing import Optional, List

from config import IMAGE_BASE_SUBPATH, MAVIN_FOLDER, get_available_drives


def build_mavin_base_path(drive: str, model_id: str, date_str: str) -> str:
    """
    Build the Mavin base directory path for a given drive, model, and date.

    Example: F:\\Files\\Image\\JF2\\2026\\03\\06\\Mavin

    Args:
        drive: Drive letter (e.g. "F").
        model_id: Model name (e.g. "JF2").
        date_str: Date in YYYYMMDD format.

    Returns:
        Full Mavin directory path.
    """
    yyyy = date_str[0:4]
    mm = date_str[4:6]
    dd = date_str[6:8]

    return os.path.join(
        f"{drive}:\\", IMAGE_BASE_SUBPATH, model_id,
        yyyy, mm, dd, MAVIN_FOLDER
    )


def build_crop_folder_path(mavin_base: str, crop_folder: str) -> str:
    """
    Build the full path to a specific crop folder under Mavin.

    Example: F:\\Files\\Image\\JF2\\2026\\03\\06\\Mavin\\Crop_A

    Args:
        mavin_base: Path to the Mavin directory.
        crop_folder: Subfolder name (e.g. "Crop_A", "Gap_DL", "HORNMARK").

    Returns:
        Full crop folder path.
    """
    return os.path.join(mavin_base, crop_folder)


def list_class_subfolders(crop_folder_path: str) -> List[str]:
    """
    List all class subfolders within a crop folder.
    Used for crop types that have class subfolders (e.g. Crop_A, Crop_B).

    Args:
        crop_folder_path: Path to the crop folder.

    Returns:
        List of full paths to class subfolders.
    """
    if not os.path.isdir(crop_folder_path):
        return []

    subfolders = []
    for entry in os.listdir(crop_folder_path):
        full_path = os.path.join(crop_folder_path, entry)
        if os.path.isdir(full_path):
            subfolders.append(full_path)

    return sorted(subfolders)


def find_mavin_across_drives(
    model_id: str,
    date_str: str,
    crop_folder: str,
    drives: List[str] = None,
) -> Optional[str]:
    """
    Scan all available drives to find a Mavin crop folder.

    Args:
        model_id: Model name (e.g. "JF2").
        date_str: Date in YYYYMMDD format.
        crop_folder: Subfolder name under Mavin (e.g. "Crop_A").
        drives: Optional list of drive letters. Defaults to auto-detect.

    Returns:
        Full path to the crop folder, or None if not found.
    """
    drive_list = drives or get_available_drives()

    for drive in drive_list:
        mavin_base = build_mavin_base_path(drive, model_id, date_str)
        crop_path = build_crop_folder_path(mavin_base, crop_folder)
        if os.path.isdir(crop_path):
            return crop_path

    return None