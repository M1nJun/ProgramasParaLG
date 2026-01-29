from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

Label = Literal["RealNG", "Overkill"]


@dataclass(frozen=True)
class LabelAction:
    """
    Represents one hotkey labeling operation for one occurrence.
    We copy SourceMap only (per your rule).
    """
    label: Label
    class_folder: str
    cell_key: str
    region: str

    src_path: Path
    dst_path: Path
