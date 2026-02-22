from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


FLOWMAP_SUFFIX = "Flowmap.jpg"


@dataclass(frozen=True)
class FetchResult:
    cell_id: str
    found_images: List[Path]
    copied_to: List[Path]
    message: str


def normalize_cell_ids(raw: str) -> List[str]:
    """
    Accepts pasted text. Splits by whitespace, comma, semicolon, etc.
    Keeps tokens that look like your cell ids (letters+digits).
    """
    tokens = re.split(r"[,\s;]+", raw.strip())
    cleaned: List[str] = []
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        # Keep as-is; just basic sanity (at least 6 chars, contains a digit)
        if len(t) >= 6 and any(ch.isdigit() for ch in t):
            cleaned.append(t)
    # de-dup while preserving order
    seen = set()
    out = []
    for x in cleaned:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def date_to_parts(date_str: str) -> Tuple[str, str, str, str]:
    """
    Input: 'YYYY-MM-DD' or 'YYYY/MM/DD' or 'YYYYMMDD'
    Output: (YYYY, MM, DD, YYYYMMDD)
    """
    s = date_str.strip()
    if re.fullmatch(r"\d{8}", s):
        yyyy, mm, dd = s[:4], s[4:6], s[6:8]
        return yyyy, mm, dd, s

    s = s.replace("/", "-")
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if not m:
        raise ValueError("Date must be YYYY-MM-DD (or YYYYMMDD). Example: 2026-02-22")
    yyyy, mm, dd = m.group(1), m.group(2), m.group(3)
    return yyyy, mm, dd, f"{yyyy}{mm}{dd}"


def find_image_dir_for_cell(day_root: Path, cell_id: str) -> Path | None:
    """
    Find the directory that contains the cell_id in its name, and has a child folder 'Image'.
    Example:
      ...\\20260222_090610_..._d62MJ74960_(OK_NG)\\Image
    We return the 'Image' directory path.
    """
    if not day_root.exists():
        return None

    # Search for directories with cell_id in the folder name, anywhere under the day root.
    # Then check if that directory has an "Image" child folder.
    # This avoids relying on specific JUDGE names (OK/NG/DL_CANDIDATE/etc).
    candidates = []
    for p in day_root.rglob(f"*{cell_id}*"):
        if p.is_dir():
            image_dir = p / "Image"
            if image_dir.exists() and image_dir.is_dir():
                candidates.append(image_dir)

    if not candidates:
        return None

    # If multiple, pick the one that has Flowmap images (best match).
    for image_dir in candidates:
        flowmaps = sorted(image_dir.glob(f"*{FLOWMAP_SUFFIX}"))
        if flowmaps:
            return image_dir

    # Otherwise, just return the first (stable order)
    return sorted(candidates)[0]


def fetch_flowmaps_for_cell(day_root: Path, cell_id: str) -> List[Path]:
    """
    Returns full paths of Flowmap.jpg images under the matching Image folder.
    """
    image_dir = find_image_dir_for_cell(day_root, cell_id)
    if image_dir is None:
        return []

    flowmaps = sorted(image_dir.glob(f"*{FLOWMAP_SUFFIX}"))
    return flowmaps


def copy_flowmaps(
    date_str: str,
    cell_ids: List[str],
    f_root: Path = Path(r"F:\Files"),
    output_root: Path = Path(r"D:\OUTPUT"),
) -> Tuple[List[FetchResult], Dict[str, int]]:
    """
    Copies Flowmap images for each cell id into:
      D:\\OUTPUT\\YYYYMMDD\\CELL_ID\\

    Returns:
      - list of FetchResult per cell
      - summary counts
    """
    yyyy, mm, dd, yyyymmdd = date_to_parts(date_str)
    day_root = f_root / yyyy / mm / dd

    results: List[FetchResult] = []
    summary = {"cells_total": 0, "cells_ok": 0, "cells_missing": 0, "images_copied": 0}

    summary["cells_total"] = len(cell_ids)

    for cell_id in cell_ids:
        found = fetch_flowmaps_for_cell(day_root, cell_id)

        if not found:
            results.append(FetchResult(cell_id, [], [], "NOT FOUND (no Image folder / no Flowmap.jpg)"))
            summary["cells_missing"] += 1
            continue

        dest_dir = output_root / yyyymmdd / cell_id
        dest_dir.mkdir(parents=True, exist_ok=True)

        copied_to: List[Path] = []
        for src in found:
            dst = dest_dir / src.name
            shutil.copy2(src, dst)
            copied_to.append(dst)

        summary["cells_ok"] += 1
        summary["images_copied"] += len(copied_to)

        # message if it isn't exactly 2 (you said it should be only 2)
        msg = "OK"
        if len(found) != 2:
            msg = f"FOUND {len(found)} (expected 2)"

        results.append(FetchResult(cell_id, found, copied_to, msg))

    return results, summary