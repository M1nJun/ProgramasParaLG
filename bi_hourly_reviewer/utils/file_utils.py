"""
File system utility functions.

Responsibilities:
    - Drive detection and validation.
    - Path construction helpers.
    - File/directory existence checks.
"""

import os
import string
from typing import List


def get_all_drives() -> List[str]:
    """
    Detect all available drive letters on the system.

    Returns:
        List of single uppercase drive letters (e.g. ["C", "D", "F"]).
    """
    drives = []
    for letter in string.ascii_uppercase:
        if os.path.exists(f"{letter}:\\"):
            drives.append(letter)
    return drives


def ensure_directory(path: str) -> str:
    """
    Create a directory if it doesn't exist.

    Args:
        path: Directory path to create.

    Returns:
        The path (for chaining).
    """
    os.makedirs(path, exist_ok=True)
    return path


def count_files_in_dir(path: str, extension: str = None) -> int:
    """
    Count files in a directory, optionally filtering by extension.

    Args:
        path: Directory path.
        extension: File extension to filter (e.g. ".jpg"). None for all files.

    Returns:
        Number of matching files.
    """
    if not os.path.isdir(path):
        return 0

    count = 0
    for entry in os.listdir(path):
        if os.path.isfile(os.path.join(path, entry)):
            if extension is None or entry.lower().endswith(extension.lower()):
                count += 1
    return count


def safe_path_join(*parts: str) -> str:
    """
    Join path parts, handling Windows drive letters correctly.
    """
    return os.path.join(*parts)