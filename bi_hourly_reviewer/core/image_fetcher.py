"""
Image fetching (copying to output directory).

Responsibilities:
    - Build the output directory structure.
    - Copy selected images from source to output.
    - Report success/failure per cell.

Does NOT locate or select images — uses image_locator and image_selector.
"""

import os
import shutil
from typing import List, Dict, Optional

from config import OUTPUT_BASE_DIR


def build_output_dir(
    date_str: str,
    hour: int,
    cell_id: str,
    judge_defect: str,
    base_dir: str = None,
) -> str:
    """
    Build the output directory path for a single cell's images.

    Structure:
        D:\\BI-HOURLY_REVIEW\\2026\\03\\06\\08\\j62SK05777 - B_R\\

    Args:
        date_str: Date in YYYYMMDD format.
        hour: Hour as integer.
        cell_id: Cell ID string.
        judge_defect: Defect type string (e.g. "B_R", "Tab_Damage").
        base_dir: Override output base. Defaults to OUTPUT_BASE_DIR.

    Returns:
        Full output directory path.
    """
    base = base_dir or OUTPUT_BASE_DIR
    yyyy = date_str[0:4]
    mm = date_str[4:6]
    dd = date_str[6:8]
    hh = f"{hour:02d}"
    folder_name = f"{cell_id} - {judge_defect}"

    return os.path.join(base, yyyy, mm, dd, hh, folder_name)


def copy_images_to_output(
    image_paths: List[str],
    output_dir: str,
) -> Dict[str, str]:
    """
    Copy image files to the output directory.

    Args:
        image_paths: List of source image file paths.
        output_dir: Destination directory.

    Returns:
        Dict mapping source path -> destination path for successfully copied files.
    """
    os.makedirs(output_dir, exist_ok=True)

    copied = {}
    for src in image_paths:
        if not os.path.isfile(src):
            continue
        fname = os.path.basename(src)
        dst = os.path.join(output_dir, fname)
        shutil.copy2(src, dst)
        copied[src] = dst

    return copied


def fetch_single_cell(
    defect_record: Dict,
    output_base: str = None,
) -> Optional[Dict]:
    """
    Full fetch pipeline for a single defect cell.

    Locates the image folder, selects the right images, and copies them
    to the output directory.

    Args:
        defect_record: Dict from defect_analyzer.build_defect_record().
        output_base: Override output base directory.

    Returns:
        Dict with fetch results, or None if images could not be found.
        Keys: output_dir, copied_files, source_folder, side, cell_id
    """
    from core.image_locator import locate_cell_images_across_drives
    from core.image_selector import select_images_from_folder

    cell_id = defect_record["cell_id"]
    model_id = defect_record["model_id"]
    date_str = defect_record["date"]
    judge = defect_record["judge"]
    judge_defect = defect_record["judge_defect"]
    side = defect_record["side"]
    time_obj = defect_record["time"]

    if time_obj is None:
        return None

    hour = time_obj.hour

    # Locate the cell folder across drives
    cell_folder = locate_cell_images_across_drives(
        model_id=model_id,
        date_str=date_str,
        hour=hour,
        judge=judge,
        cell_id=cell_id,
    )

    if cell_folder is None:
        return None

    # Select the images for the defect side
    selected_images = select_images_from_folder(cell_folder, side)

    if not selected_images:
        return None

    # Build output dir and copy
    output_dir = build_output_dir(date_str, hour, cell_id, judge_defect, output_base)
    copied = copy_images_to_output(selected_images, output_dir)

    return {
        "cell_id": cell_id,
        "side": side,
        "judge": judge,
        "judge_defect": judge_defect,
        "source_folder": cell_folder,
        "output_dir": output_dir,
        "copied_files": copied,
        "image_count": len(copied),
    }