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
    Overwrite if exists (per your rule).

    Returns LabelAction that can be undone (move back).
    """
    if not occurrence.source_path:
        raise ValueError("Selected occurrence has no SourceMap file.")

    src = Path(occurrence.source_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"SourceMap file not found: {src}")

    dest_dir = dest_dir_for(Path(human_root), occurrence.class_folder, label)
    ensure_dir(dest_dir)

    dst = dest_dir / src.name

    # Overwrite allowed
    if dst.exists():
        dst.unlink()

    # MOVE
    shutil.move(str(src), str(dst))

    return LabelAction(
        label=label,
        class_folder=occurrence.class_folder,
        cell_key=occurrence.cell_key,
        region=occurrence.region,
        src_path=src,     # original location
        dst_path=dst,     # moved-to location
    )


def undo(action: LabelAction) -> None:
    """
    Undo for move-mode: move file back from HumanReview to original src_path.
    Overwrite original if exists.
    """
    src_back = Path(action.src_path)
    moved = Path(action.dst_path)

    if not moved.exists():
        # nothing to undo
        return

    # Ensure original directory exists
    src_back.parent.mkdir(parents=True, exist_ok=True)

    if src_back.exists():
        src_back.unlink()

    shutil.move(str(moved), str(src_back))
