from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

DEFAULT_MODEL = "JF2"

# Your fixed path base (drive letter may change)
BASE_PARTS = ("Files", "Image")

# Fixed inner path
PIPELINE_PARTS = ("Mavin", "Crop_B")

# Only these are excluded per your requirement
EXCLUDED_CLASS_FOLDERS = {"01_ok_anode", "01_ok_cathode"}

# Drive scan order: E: then F: ... up to Z:
DEFAULT_DRIVES: Tuple[str, ...] = tuple(chr(c) for c in range(ord("E"), ord("Z") + 1))

# File marker
SOURCEMAP_SUFFIX = "SourceMap.jpg"


@dataclass(frozen=True)
class FoundRoot:
    drive: str
    path: Path
