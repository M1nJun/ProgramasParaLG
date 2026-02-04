from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, List


IMAGE_DRIVES = ["E", "F", "G"]
CSV_DRIVE = "D"


def unc_root(ip: str, share: str) -> Path:
    # UNC path like \\10.0.0.1\E
    return Path(rf"\\{ip}\{share}")


def image_base(ip: str, drive_letter: str) -> Path:
    # \\ip\E\Files\Image
    return unc_root(ip, drive_letter) / "Files" / "Image"


def csv_base(ip: str) -> Path:
    # \\ip\D\Files\Data\Result\Day
    return unc_root(ip, CSV_DRIVE) / "Files" / "Data" / "Result" / "Day"


def crop_b_root(image_base_dir: Path, model: str, day: date) -> Path:
    # ...\JF2\YYYY\MM\DD\Mavin\Crop_B
    return (
        image_base_dir
        / model
        / f"{day.year:04d}"
        / f"{day.month:02d}"
        / f"{day.day:02d}"
        / "Mavin"
        / "Crop_B"
    )
