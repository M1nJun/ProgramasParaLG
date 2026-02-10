from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .filename_parser import parse_image_filename


POLARITIES = ["CATHODE", "ANODE"]


def normalize_class_folder(folder_name: str) -> str:
    s = folder_name.strip()
    if "_" in s:
        head, tail = s.split("_", 1)
        if head.isdigit():
            return tail.strip().upper()
    return s.strip().upper()


@dataclass
class OccurrenceItem:
    class_folder: str
    class_key: str
    cell_key: str
    region: str
    polarity: str  # "ANODE" or "CATHODE"
    source_path: Optional[Path] = None
    active_path: Optional[Path] = None


@dataclass
class ViewIndex:
    out_dir: Path
    # polarity -> class_folder -> list[OccurrenceItem]
    classes: Dict[str, Dict[str, List[OccurrenceItem]]]
    # polarity -> class_key -> class_folder
    class_key_to_folder: Dict[str, Dict[str, str]]


def _iter_class_dirs_under(root: Path) -> List[Path]:
    return sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.name.lower())


def build_view_index(out_dir: Path) -> ViewIndex:
    out_dir = out_dir.expanduser().resolve()

    classes: Dict[str, Dict[str, List[OccurrenceItem]]] = {}
    class_key_to_folder: Dict[str, Dict[str, str]] = {}

    if not out_dir.exists() or not out_dir.is_dir():
        return ViewIndex(out_dir=out_dir, classes={}, class_key_to_folder={})

    # Detect new polarity layout
    polarity_roots: List[Tuple[str, Path]] = []
    for pol in POLARITIES:
        p = out_dir / pol
        if p.exists() and p.is_dir():
            polarity_roots.append((pol, p))

    # Backward compatible: no polarity folders -> treat everything as "CATHODE" bucket (or "ALL")
    if not polarity_roots:
        polarity_roots = [("CATHODE", out_dir)]

    # temp: (polarity, folder, cell, region) -> OccurrenceItem
    bucket: Dict[Tuple[str, str, str, str], OccurrenceItem] = {}

    for polarity, root in polarity_roots:
        classes.setdefault(polarity, {})
        class_key_to_folder.setdefault(polarity, {})

        for class_dir in _iter_class_dirs_under(root):
            folder_name = class_dir.name
            class_key = normalize_class_folder(folder_name)
            class_key_to_folder[polarity][class_key] = folder_name

            for f in class_dir.glob("*.jpg"):
                parsed = parse_image_filename(f)
                if not parsed:
                    continue

                key = (polarity, folder_name, parsed.cell_key, parsed.region)
                item = bucket.get(key)
                if not item:
                    item = OccurrenceItem(
                        class_folder=folder_name,
                        class_key=class_key,
                        cell_key=parsed.cell_key,
                        region=parsed.region,
                        polarity=polarity,
                    )
                    bucket[key] = item

                if parsed.map_type == "SourceMap":
                    item.source_path = f
                elif parsed.map_type == "ActiveMap":
                    item.active_path = f

    # finalize classes dict
    for (polarity, folder_name, _, _), item in bucket.items():
        classes.setdefault(polarity, {}).setdefault(folder_name, []).append(item)

    for polarity in classes:
        for folder_name in classes[polarity]:
            classes[polarity][folder_name].sort(key=lambda x: (x.cell_key, x.region))

    return ViewIndex(out_dir=out_dir, classes=classes, class_key_to_folder=class_key_to_folder)


def resolve_folder_for_class_key(index: ViewIndex, polarity: str, class_key: str) -> Optional[str]:
    if not class_key:
        return None
    pol = (polarity or "").strip().upper()
    key = class_key.strip().upper()
    return (index.class_key_to_folder.get(pol, {}) or {}).get(key)