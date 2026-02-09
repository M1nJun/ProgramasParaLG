from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List


SETTINGS_FILE = Path(__file__).resolve().parent / "settings.json"


@dataclass
class AreaSettings:
    # Session
    model: str = "JF2"
    out_dir: str = ""
    csv_dir: str = r"D:\Files\Data\Result\Day"

    date_mode: str = "Single date"
    single_date: str = ""
    range_start: str = ""
    range_end: str = ""
    specific_dates: List[str] = field(default_factory=list)

    selected_pcs: List[str] = field(default_factory=list)

    # Fetch
    include_activemap: bool = False

    # Summary
    summary_csv_paths: List[str] = field(default_factory=list)
    summary_top_n: int = 20

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "AreaSettings":
        s = AreaSettings()
        s.model = str(d.get("model", s.model))
        s.out_dir = str(d.get("out_dir", s.out_dir))
        s.csv_dir = str(d.get("csv_dir", s.csv_dir))

        s.date_mode = str(d.get("date_mode", s.date_mode))
        s.single_date = str(d.get("single_date", s.single_date))
        s.range_start = str(d.get("range_start", s.range_start))
        s.range_end = str(d.get("range_end", s.range_end))
        s.specific_dates = list(d.get("specific_dates", s.specific_dates) or [])

        s.selected_pcs = list(d.get("selected_pcs", s.selected_pcs) or [])

        s.include_activemap = bool(d.get("include_activemap", s.include_activemap))

        s.summary_csv_paths = list(d.get("summary_csv_paths", s.summary_csv_paths) or [])
        s.summary_top_n = int(d.get("summary_top_n", s.summary_top_n))
        return s

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Settings:
    # Per-area settings (new)
    area_a: AreaSettings = field(default_factory=AreaSettings)
    area_b: AreaSettings = field(default_factory=AreaSettings)

    # Window
    window_geometry_b64: str = ""

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Settings":
        s = Settings()

        # New format
        if isinstance(d.get("area_a"), dict):
            s.area_a = AreaSettings.from_dict(d["area_a"])
        if isinstance(d.get("area_b"), dict):
            s.area_b = AreaSettings.from_dict(d["area_b"])

        # Backward compat (old single-session format):
        # if area_a/area_b were not present, hydrate both from top-level keys
        if "area_a" not in d and "area_b" not in d:
            legacy = AreaSettings.from_dict(d)
            s.area_a = AreaSettings.from_dict(legacy.to_dict())
            s.area_b = AreaSettings.from_dict(legacy.to_dict())

        s.window_geometry_b64 = str(d.get("window_geometry_b64", s.window_geometry_b64))
        return s

    def to_dict(self) -> Dict[str, Any]:
        return {
            "area_a": self.area_a.to_dict(),
            "area_b": self.area_b.to_dict(),
            "window_geometry_b64": self.window_geometry_b64,
        }


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