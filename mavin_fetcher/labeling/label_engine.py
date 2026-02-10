from __future__ import annotations

import shutil
from pathlib import Path

from mavin_fetcher.view_index import OccurrenceItem
from .types import Label, LabelAction
from .pathing import dest_dir_for, ensure_dir


def apply_label(
    occurrence: OccurrenceItem,
    *,
    label: Label,
    human_root: Path,
) -> LabelAction:
    """
    MOVE SourceMap only to HumanReview mirror folders.
    Overwrite if exists.

    Destination includes polarity:
      HumanReview\\<POLARITY>\\<ClassFolder>\\<Label>\\
    """
    if not occurrence.source_path:
        raise ValueError("Selected occurrence has no SourceMap file.")

    src = Path(occurrence.source_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"SourceMap file not found: {src}")

    dest_dir = dest_dir_for(Path(human_root), occurrence.polarity, occurrence.class_folder, label)
    ensure_dir(dest_dir)

    dst = dest_dir / src.name

    if dst.exists():
        dst.unlink()

    shutil.move(str(src), str(dst))

    return LabelAction(
        label=label,
        polarity=occurrence.polarity,
        class_folder=occurrence.class_folder,
        cell_key=occurrence.cell_key,
        region=occurrence.region,
        src_path=src,
        dst_path=dst,
    )


def undo(action: LabelAction) -> None:
    src_back = Path(action.src_path)
    moved = Path(action.dst_path)

    if not moved.exists():
        return

    src_back.parent.mkdir(parents=True, exist_ok=True)

    if src_back.exists():
        src_back.unlink()

    shutil.move(str(moved), str(src_back))