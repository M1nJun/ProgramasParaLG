from __future__ import annotations

from pathlib import Path

from .config import SOURCEMAP_SUFFIX


def sourcemap_to_activemap_path(src: Path) -> Path:
    """
    Converts:
      ..._SourceMap.jpg -> ..._ActiveMap.jpg

    Assumes src is a SourceMap file path.
    """
    name = src.name
    if not name.endswith(SOURCEMAP_SUFFIX):
        # fallback: naive replace if someone passes unexpected name
        return src.with_name(name.replace("SourceMap.jpg", "ActiveMap.jpg"))

    active_name = name[:-len(SOURCEMAP_SUFFIX)] + "ActiveMap.jpg"
    return src.with_name(active_name)
