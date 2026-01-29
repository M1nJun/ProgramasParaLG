from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List

from mavin_fetcher.date_utils import parse_ymd, date_range_inclusive, parse_dates_csv


@dataclass
class SessionState:
    # Shared selection used across Fetch/Summary/Viewer
    model: str = "JF2"
    out_dir: str = ""
    out_dir_user_set: bool = False
    csv_dir: str = r"D:\Files\Data\Result\Day"

    # Date selection
    date_mode: str = "Single date"
    single_date: str = ""        # yyyy-MM-dd
    range_start: str = ""        # yyyy-MM-dd
    range_end: str = ""          # yyyy-MM-dd
    specific_dates: List[str] = field(default_factory=list)

    def to_days(self) -> List[date]:
        mode = (self.date_mode or "Single date").strip()

        if mode == "Single date":
            if not self.single_date:
                return []
            return [parse_ymd(self.single_date)]

        if mode == "Date range":
            if not self.range_start or not self.range_end:
                return []
            return date_range_inclusive(parse_ymd(self.range_start), parse_ymd(self.range_end))

        if mode == "Specific dates":
            txt = ",".join(self.specific_dates or [])
            return parse_dates_csv(txt)

        return []
