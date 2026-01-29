from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from mavin_fetcher.date_utils import parse_ymd, date_range_inclusive, parse_dates_csv
from mavin_fetcher.engine_fetch import fetch_images


@dataclass(frozen=True)
class FetchTaskConfig:
    date_mode: str  # "Single date" | "Date range" | "Specific dates"
    date_text: str
    out_dir: str
    model: str
    drives_text: str
    include_activemap: bool


class FetchWorker(QThread):
    progress_pct = pyqtSignal(int)             # 0..100
    log = pyqtSignal(str)
    status = pyqtSignal(int, int, str, str)    # done, total, class_name, filename  <-- NEW
    done = pyqtSignal(bool, str)               # (success, message)

    def __init__(self, cfg: FetchTaskConfig):
        super().__init__()
        self.cfg = cfg
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def _is_cancelled(self) -> bool:
        return self._cancel

    def _parse_drives(self) -> list[str]:
        parts = [x.strip() for x in (self.cfg.drives_text or "").split(",") if x.strip()]
        return parts if parts else ["E", "F", "G"]

    def _parse_days(self) -> list:
        txt = (self.cfg.date_text or "").strip()
        if self.cfg.date_mode == "Single date":
            return [parse_ymd(txt)]

        if self.cfg.date_mode == "Date range":
            cleaned = txt.replace("to", " ").replace(",", " ")
            parts = [p for p in cleaned.split() if p]
            if len(parts) != 2:
                raise ValueError("Date range must have exactly 2 dates: START END")
            return date_range_inclusive(parse_ymd(parts[0]), parse_ymd(parts[1]))

        if self.cfg.date_mode == "Specific dates":
            return parse_dates_csv(txt)

        raise ValueError(f"Unknown date mode: {self.cfg.date_mode}")

    def run(self) -> None:
        try:
            days = self._parse_days()
            out_dir = Path(self.cfg.out_dir).expanduser().resolve()
            model = (self.cfg.model or "JF2").strip()
            drives = self._parse_drives()

            # existing: (done,total) -> percent
            def on_progress(done: int, total: int) -> None:
                if total <= 0:
                    self.progress_pct.emit(0)
                    return
                self.progress_pct.emit(int(done * 100 / total))

            # NEW: detailed status for labels (Copied X/Y, class, filename)
            def on_detail(done: int, total: int, class_name: str, filename: str) -> None:
                self.status.emit(done, total, class_name, filename)

            stats = fetch_images(
                days=days,
                out_dir=out_dir,
                model=model,
                drives=drives,
                include_activemap=bool(self.cfg.include_activemap),
                log=self.log.emit,
                progress=on_progress,
                detail_progress=on_detail,     # <-- NEW (requires engine_fetch.py change)
                is_cancelled=self._is_cancelled,
            )

            if self._cancel:
                self.done.emit(False, "Cancelled.")
                return

            msg = f"Done. Copied {stats.total_copied} (overwrote {stats.total_overwritten}). Missing days: {stats.missing_days}"
            self.done.emit(True, msg)

        except Exception as e:
            self.done.emit(False, f"Error: {e}")
