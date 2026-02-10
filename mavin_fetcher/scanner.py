from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

from .config import EXCLUDED_CLASS_FOLDERS, SOURCEMAP_SUFFIX
from .pairing import sourcemap_to_activemap_path


@dataclass(frozen=True)
class ScanResult:
    files_by_class: Dict[str, List[Path]]
    missing_activemap_count: int
    included_activemap_count: int


def list_class_folders(crop_root: Path, excluded: Set[str]) -> List[Path]:
    out: List[Path] = []
    for child in crop_root.iterdir():
        if not child.is_dir():
            continue
        if child.name.lower() in excluded:
            continue
        out.append(child)
    return sorted(out, key=lambda p: p.name.lower())


def collect_sourcemaps(class_folder: Path) -> List[Path]:
    files: List[Path] = []
    for f in class_folder.iterdir():
        if f.is_file() and f.name.endswith(SOURCEMAP_SUFFIX):
            files.append(f)
    return sorted(files, key=lambda p: p.name.lower())


def scan(
    crop_root: Path,
    include_activemap: bool,
    excluded_class_folders: Optional[Set[str]] = None,
) -> ScanResult:
    excluded = excluded_class_folders if excluded_class_folders is not None else EXCLUDED_CLASS_FOLDERS

    files_by_class: Dict[str, List[Path]] = {}
    missing_active = 0
    included_active = 0

    for class_dir in list_class_folders(crop_root, excluded):
        srcs = collect_sourcemaps(class_dir)
        if not srcs:
            files_by_class[class_dir.name] = []
            continue

        out_files: List[Path] = []
        for src in srcs:
            out_files.append(src)
            if include_activemap:
                active = sourcemap_to_activemap_path(src)
                if active.exists() and active.is_file():
                    out_files.append(active)
                    included_active += 1
                else:
                    missing_active += 1

        files_by_class[class_dir.name] = out_files

    return ScanResult(
        files_by_class=files_by_class,
        missing_activemap_count=missing_active,
        included_activemap_count=included_active,
    )