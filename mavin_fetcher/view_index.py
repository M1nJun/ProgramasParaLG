from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .filename_parser import parse_image_filename


REGIONS = ["LOWER_B_L", "LOWER_B_R", "UPPER_B_L", "UPPER_B_R"]


def normalize_class_folder(folder_name: str) -> str:
    """
    Convert:
      05_NG_CRITICAL -> NG_CRITICAL
      06_OK_ROI      -> OK_ROI
      NG_FOLDED      -> NG_FOLDED
    """
    s = folder_name.strip()
    if "_" in s:
        head, tail = s.split("_", 1)
        if head.isdigit():
            return tail.strip().upper()
    return s.strip().upper()


@dataclass
class OccurrenceItem:
    """
    One occurrence = one cell in one region (with optional source/active files).
    """
    class_folder: str      # actual folder name e.g. 05_NG_CRITICAL
    class_key: str         # normalized e.g. NG_CRITICAL
    cell_key: str
    region: str            # LOWER_B_L etc
    source_path: Optional[Path] = None
    active_path: Optional[Path] = None


@dataclass
class ViewIndex:
    """
    Index built from fetch output folder.
    classes maps folder-name -> list[OccurrenceItem]
    class_key_to_folder helps map NG_CRITICAL -> 05_NG_CRITICAL
    """
    out_dir: Path
    classes: Dict[str, List[OccurrenceItem]]
    class_key_to_folder: Dict[str, str]


def build_view_index(out_dir: Path) -> ViewIndex:
    out_dir = out_dir.expanduser().resolve()
    classes: Dict[str, List[OccurrenceItem]] = {}
    class_key_to_folder: Dict[str, str] = {}

    if not out_dir.exists() or not out_dir.is_dir():
        return ViewIndex(out_dir=out_dir, classes={}, class_key_to_folder={})

    # temp map: (folder, cell_key, region) -> OccurrenceItem
    bucket: Dict[Tuple[str, str, str], OccurrenceItem] = {}

    for class_dir in sorted([p for p in out_dir.iterdir() if p.is_dir()]):
        folder_name = class_dir.name
        class_key = normalize_class_folder(folder_name)
        class_key_to_folder[class_key] = folder_name

        for f in class_dir.glob("*.jpg"):
            parsed = parse_image_filename(f)
            if not parsed:
                continue

            key = (folder_name, parsed.cell_key, parsed.region)
            item = bucket.get(key)
            if not item:
                item = OccurrenceItem(
                    class_folder=folder_name,
                    class_key=class_key,
                    cell_key=parsed.cell_key,
                    region=parsed.region,
                )
                bucket[key] = item

            if parsed.map_type == "SourceMap":
                item.source_path = f
            elif parsed.map_type == "ActiveMap":
                item.active_path = f

    # finalize classes dict
    for (folder_name, _, _), item in bucket.items():
        classes.setdefault(folder_name, []).append(item)

    # sort each class list by cell_key then region
    for folder_name in classes:
        classes[folder_name].sort(key=lambda x: (x.cell_key, x.region))

    return ViewIndex(out_dir=out_dir, classes=classes, class_key_to_folder=class_key_to_folder)


def resolve_folder_for_class_key(index: ViewIndex, class_key: str) -> Optional[str]:
    """
    Map NG_CRITICAL -> 05_NG_CRITICAL if found.
    """
    if not class_key:
        return None
    key = class_key.strip().upper()
    return index.class_key_to_folder.get(key)
