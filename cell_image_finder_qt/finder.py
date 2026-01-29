
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, List, Tuple
import shutil
import re

CANDIDATE_SUBDIRS = [
    Path("NG"),
    Path("OK") / "DL_CANDIDATE",
    Path("OK") / "DL_OK",
]

@dataclass
class MatchResult:
    cell_id: str
    folder: Path
    category_dir: Path
    img0: Optional[Path]
    img1: Optional[Path]
    timestamp_key: str  # sortable key extracted from folder name (YYYYMMDD_HHMMSS)

def parse_date(date_str: str) -> Tuple[str, str, str]:
    """
    Accepts YYYY-MM-DD or YYYY/MM/DD.
    Returns (YYYY, MM, DD) with MM/DD zero-padded.
    """
    s = date_str.strip().replace("/", "-")
    parts = s.split("-")
    if len(parts) != 3:
        raise ValueError("Date must be YYYY-MM-DD (or YYYY/MM/DD).")
    yyyy, mm, dd = parts
    if len(yyyy) != 4 or not yyyy.isdigit():
        raise ValueError("Year must be 4 digits.")
    if not mm.isdigit() or not dd.isdigit():
        raise ValueError("Month and Day must be numeric.")
    return yyyy, mm.zfill(2), dd.zfill(2)

def iter_hour_dirs(date_root: Path) -> Iterable[Path]:
    for h in range(24):
        yield date_root / f"{h:02d}"

def _safe_listdir(p: Path) -> List[Path]:
    try:
        return list(p.iterdir())
    except Exception:
        return []

def find_matching_image_folders(search_dir: Path, cell_id: str) -> List[Path]:
    """
    Returns immediate subfolders in search_dir whose name contains _{cell_id}
    """
    if not search_dir.exists() or not search_dir.is_dir():
        return []
    needle = f"_{cell_id}"
    matches: List[Path] = []
    for p in _safe_listdir(search_dir):
        if p.is_dir() and needle in p.name:
            matches.append(p)
    return matches

def extract_timestamp_key(folder_name: str) -> str:
    """
    Folder name format example:
      20260117_152731_8A7EL155K1_h5CMK04138
    We extract '20260117_152731' as a sortable key.
    If not found, return empty string (least).
    """
    m = re.match(r"^(\d{8}_\d{6})_", folder_name)
    return m.group(1) if m else ""

def find_required_images(image_folder: Path, cell_id: str) -> Tuple[Optional[Path], Optional[Path]]:
    pat0 = f"*_{cell_id}_EXT_DL_0_2.jpg"
    pat1 = f"*_{cell_id}_EXT_DL_1_2.jpg"
    img0 = next(iter(image_folder.glob(pat0)), None)
    img1 = next(iter(image_folder.glob(pat1)), None)
    return img0, img1

def search_matches_for_cell(base_dir: Path, yyyy: str, mm: str, dd: str, cell_id: str) -> List[MatchResult]:
    date_root = base_dir / yyyy / mm / dd
    results: List[MatchResult] = []
    if not date_root.exists():
        return results

    for hour_dir in iter_hour_dirs(date_root):
        if not hour_dir.exists():
            continue
        for sub in CANDIDATE_SUBDIRS:
            candidate_dir = hour_dir / sub
            folders = find_matching_image_folders(candidate_dir, cell_id)
            for f in folders:
                img0, img1 = find_required_images(f, cell_id)
                results.append(
                    MatchResult(
                        cell_id=cell_id,
                        folder=f,
                        category_dir=candidate_dir,
                        img0=img0,
                        img1=img1,
                        timestamp_key=extract_timestamp_key(f.name),
                    )
                )
    return results

def choose_best_match(matches: List[MatchResult]) -> Optional[MatchResult]:
    """
    Choose the latest by timestamp_key; tie-break by folder name.
    """
    if not matches:
        return None
    return sorted(matches, key=lambda r: (r.timestamp_key, r.folder.name))[-1]

def copy_images(result: MatchResult, out_dir: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """
    Copy img0/img1 into out_dir/<cell_id>/ keeping filenames.
    Returns destination paths (or None for missing).
    """
    dest_dir = out_dir / result.cell_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest0 = dest1 = None

    if result.img0 and result.img0.exists():
        dest0 = dest_dir / result.img0.name
        shutil.copy2(result.img0, dest0)
    if result.img1 and result.img1.exists():
        dest1 = dest_dir / result.img1.name
        shutil.copy2(result.img1, dest1)

    return dest0, dest1
