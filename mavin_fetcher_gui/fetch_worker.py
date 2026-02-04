from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from PyQt6.QtCore import QThread, pyqtSignal

from mavin_fetcher.date_utils import parse_ymd, date_range_inclusive, parse_dates_csv
from mavin_fetcher.pc_registry import load_registry
from mavin_fetcher.engine_fetch_remote import fetch_images_remote


@dataclass(frozen=True)
class FetchTaskConfig:
    date_mode: str
    date_text: str
    out_dir: str
    model: str
    selected_pcs: List[str]
    include_activemap: bool


class FetchWorker(QThread):
    progress_pct = pyqtSignal(int)
    status = pyqtSignal(int, int, str, str)  # done,total,class,file
    log = pyqtSignal(str)
    done = pyqtSignal(bool, str)

    def __init__(self, cfg: FetchTaskConfig):
        super().__init__()
        self.cfg = cfg
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def _is_cancelled(self) -> bool:
        return self._cancelled

    def _emit_progress(self, done: int, total: int) -> None:
        pct = int((done / total) * 100) if total > 0 else 0
        self.progress_pct.emit(pct)

    def _emit_detail(self, done: int, total: int, class_name: str, filename: str) -> None:
        self.status.emit(done, total, class_name, filename)
        self._emit_progress(done, total)

    def _resolve_days(self) -> list:
        mode = (self.cfg.date_mode or "").strip()
        text = (self.cfg.date_text or "").strip()

        if mode == "Single date":
            return [parse_ymd(text)]
        if mode == "Date range":
            parts = text.split()
            return date_range_inclusive(parse_ymd(parts[0]), parse_ymd(parts[1]))
        # Specific dates
        return parse_dates_csv(text)

    def run(self) -> None:
        try:
            reg = load_registry()
            pcs = [reg[k] for k in self.cfg.selected_pcs if k in reg]
            if not pcs:
                self.done.emit(False, "No valid PCs selected (check pcs.json and selection).")
                return

            days = self._resolve_days()
            out_dir = Path(self.cfg.out_dir).expanduser().resolve()

            stats = fetch_images_remote(
                pcs=pcs,
                days=days,
                out_dir=out_dir,
                model=self.cfg.model,
                include_activemap=self.cfg.include_activemap,
                log=self.log.emit,
                progress=lambda d, t: self._emit_progress(d, t),
                detail_progress=lambda d, t, c, f: self._emit_detail(d, t, c, f),
                is_cancelled=self._is_cancelled,
            )

            if self._cancelled:
                self.done.emit(False, "Cancelled.")
                return

            msg = f"Remote fetch done. Copied={stats.total_copied}, Overwrote={stats.total_overwritten}, MissingPCs={stats.missing_pcs}"
            self.done.emit(True, msg)

        except Exception as e:
            self.done.emit(False, f"Error: {e}")
