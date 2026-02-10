from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Label = Literal["RealNG", "Overkill"]


@dataclass(frozen=True)
class LabelAction:
    label: Label
    polarity: str          # "ANODE" or "CATHODE"
    class_folder: str
    cell_key: str
    region: str
    src_path: Path
    dst_path: Path