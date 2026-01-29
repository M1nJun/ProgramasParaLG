from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable, Tuple


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def copy_overwrite(files: Iterable[Path], dest_dir: Path) -> Tuple[int, int]:
    """
    Copies files into dest_dir.
    Overwrites existing files (per your collision rule).
    Returns (copied_count, overwritten_count)
    """
    ensure_dir(dest_dir)

    copied = 0
    overwritten = 0

    for src in files:
        dst = dest_dir / src.name
        if dst.exists():
            overwritten += 1
        shutil.copy2(src, dst)
        copied += 1

    return copied, overwritten
