from __future__ import annotations

from pathlib import Path

from .types import Label


def human_root_from_output(output_dir: Path) -> Path:
    return output_dir.expanduser().resolve() / "HumanReview"


def dest_dir_for(human_root: Path, class_folder: str, label: Label) -> Path:
    """
    <HumanRoot>\<ClassFolder>\<Label>\
    """
    return human_root / class_folder / label


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)
