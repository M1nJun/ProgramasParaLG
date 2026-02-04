from __future__ import annotations

import sys
from pathlib import Path


def exe_dir() -> Path:
    """
    Directory where the executable lives (PyInstaller) OR repo root when running with python.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "executable"):
        return Path(sys.executable).resolve().parent
    # dev mode: assume repo root is current working directory
    return Path.cwd().resolve()


def find_file_near_exe(filename: str) -> Path:
    return exe_dir() / filename
