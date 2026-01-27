from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

MAVIN_DEFAULT = Path(r"C:\VisionPC\Bin\MAVIN")
MAVIN_PARENT = Path(r"C:\VisionPC\Bin")
DL_VERSION_DIRNAME = "DL_VERSION"


@dataclass(frozen=True)
class MavinRoot:
    path: Path
    discovered: bool  # True if found by scanning, False if default path existed


def locate_mavin_root() -> Optional[MavinRoot]:
    """
    Windows paths are case-insensitive, but sometimes the folder is spelled 'mavin'.
    We try the default path first; if it doesn't exist, we scan C:\\VisionPC\\Bin
    for a directory name matching MAVIN case-insensitively.
    """
    if MAVIN_DEFAULT.exists() and MAVIN_DEFAULT.is_dir():
        return MavinRoot(MAVIN_DEFAULT, discovered=False)

    if MAVIN_PARENT.exists() and MAVIN_PARENT.is_dir():
        for child in MAVIN_PARENT.iterdir():
            if child.is_dir() and child.name.lower() == "mavin":
                return MavinRoot(child, discovered=True)

    return None


def list_model_folders(mavin_root: Path) -> List[Path]:
    """
    Return immediate subdirectories under MAVIN that look like model folders.
    We keep it flexible: include all subdirs, but sort with Model_* first.
    """
    if not mavin_root.exists():
        return []
    dirs = [p for p in mavin_root.iterdir() if p.is_dir()]

    def key(p: Path):
        return (0 if p.name.lower().startswith("model_") else 1, p.name.lower())

    return sorted(dirs, key=key)


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def unique_child_dir(parent: Path, name: str) -> Path:
    """
    Returns a non-existing directory path under parent by appending _1, _2, ...
    """
    candidate = parent / name
    if not candidate.exists():
        return candidate
    i = 1
    while True:
        c = parent / f"{name}_{i}"
        if not c.exists():
            return c
        i += 1


def iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def count_files(root: Path) -> int:
    return sum(1 for _ in iter_files(root))


def copy_overwrite_only(src_root: Path, dst_root: Path, *, on_file_copied=None) -> None:
    """
    Copy files/folders from src_root into dst_root.
    - Existing files are overwritten
    - Existing folders are reused
    - Files/folders that exist in dst but not in src are left untouched
    """
    src_root = src_root.resolve()
    dst_root = dst_root.resolve()
    if not src_root.exists() or not src_root.is_dir():
        raise FileNotFoundError(f"Source folder not found: {src_root}")
    if not dst_root.exists() or not dst_root.is_dir():
        raise FileNotFoundError(f"Target folder not found: {dst_root}")

    for src_path in src_root.rglob("*"):
        rel = src_path.relative_to(src_root)
        dst_path = dst_root / rel
        if src_path.is_dir():
            dst_path.mkdir(parents=True, exist_ok=True)
        else:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            if on_file_copied:
                on_file_copied(src_path, dst_path)


def backup_source_into_dl_version(src_root: Path, model_folder: Path) -> Path:
    """
    Ensure model_folder/DL_VERSION exists.
    Copy the entire src_root folder into DL_VERSION/<src_folder_name> (or <name>_1 if exists).
    Returns the created backup directory path.
    """
    src_root = src_root.resolve()
    model_folder = model_folder.resolve()

    dl_version = model_folder / DL_VERSION_DIRNAME
    ensure_dir(dl_version)

    backup_dir = unique_child_dir(dl_version, src_root.name)
    ensure_dir(backup_dir)

    def _copy_item(src: Path, dst: Path) -> None:
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            for child in src.iterdir():
                _copy_item(child, dst / child.name)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    for child in src_root.iterdir():
        _copy_item(child, backup_dir / child.name)

    return backup_dir
