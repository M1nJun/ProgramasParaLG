from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List


SETTINGS_FILE = Path(__file__).resolve().parent / "settings.json"


@dataclass
class Settings:
    # ---- Session-shared ----
    model: str = "JF2"
    out_dir: str = r"C:\Temp\CropB_Fetch"
    csv_dir: str = r"D:\Files\Data\Result\Day"

    # Date selection persistence
    date_mode: str = "Single date"
    single_date: str = ""
    range_start: str = ""
    range_end: str = ""
    specific_dates: List[str] = field(default_factory=list)

    # ---- Fetch tab ----
    drives_text: str = "E,F,G"
    include_activemap: bool = False

    # ---- Summary tab ----
    summary_csv_paths: List[str] = field(default_factory=list)
    summary_top_n: int = 20

    # ---- Window ----
    window_geometry_b64: str = ""

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Settings":
        s = Settings()
        s.model = str(d.get("model", s.model))
        s.out_dir = str(d.get("out_dir", s.out_dir))
        s.csv_dir = str(d.get("csv_dir", s.csv_dir))

        s.date_mode = str(d.get("date_mode", s.date_mode))
        s.single_date = str(d.get("single_date", s.single_date))
        s.range_start = str(d.get("range_start", s.range_start))
        s.range_end = str(d.get("range_end", s.range_end))
        s.specific_dates = list(d.get("specific_dates", s.specific_dates) or [])

        s.drives_text = str(d.get("drives_text", s.drives_text))
        s.include_activemap = bool(d.get("include_activemap", s.include_activemap))

        s.summary_csv_paths = list(d.get("summary_csv_paths", s.summary_csv_paths) or [])
        s.summary_top_n = int(d.get("summary_top_n", s.summary_top_n))

        s.window_geometry_b64 = str(d.get("window_geometry_b64", s.window_geometry_b64))
        return s

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def load_settings() -> Settings:
    try:
        if SETTINGS_FILE.exists():
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return Settings.from_dict(data)
    except Exception:
        pass
    return Settings()


def save_settings(s: Settings) -> None:
    SETTINGS_FILE.write_text(json.dumps(s.to_dict(), indent=2), encoding="utf-8")
