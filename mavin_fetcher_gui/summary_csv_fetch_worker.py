from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from PyQt6.QtCore import QThread, pyqtSignal

from mavin_fetcher.pc_registry import load_registry
from mavin_fetcher.engine_csv_fetch_remote import fetch_csvs_remote
from mavin_fetcher.date_utils import parse_ymd, date_range_inclusive, parse_dates_csv


@dataclass(frozen=True)
class SummaryCsvFetchConfig:
    date_mode: str
    date_text: str
    out_dir: str
    model: str
    selected_pcs: List[str]


class SummaryCsvFetchWorker(QThread):
    progress_pct = pyqtSignal(int)       # 0..100
    status = pyqtSignal(int, int)        # done_steps, total_steps
    log = pyqtSignal(str)
    done = pyqtSignal(bool, str, object)  # success, message, cached_paths(list[str])

    def __init__(self, cfg: SummaryCsvFetchConfig):
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
        self.status.emit(done, total)

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
            pcs = [reg[k] for k in (self.cfg.selected_pcs or []) if k in reg]
            if not pcs:
                self.done.emit(False, "No valid PCs selected (check pcs.json and selection).", [])
                return

            out_dir = Path(self.cfg.out_dir).expanduser().resolve()
            if not str(out_dir).strip():
                self.done.emit(False, "Output folder is not set in Session (out_dir).", [])
                return

            days = self._resolve_days()
            if not days:
                self.done.emit(False, "No valid day(s) selected in Session.", [])
                return

            total_steps = len(pcs) * max(1, len(days))
            self._emit_progress(0, total_steps)

            cached, stats = fetch_csvs_remote(
                pcs=pcs,
                days=days,
                out_dir=out_dir,
                model=self.cfg.model,
                log=self.log.emit,
                progress=lambda d, t: self._emit_progress(d, t),
                is_cancelled=self._is_cancelled,
            )

            if self._cancelled:
                self.done.emit(False, "Cancelled.", [])
                return

            msg = (
                f"Fetched CSVs. cached={len(cached)}, copied={stats.total_copied}, "
                f"overwritten={stats.total_overwritten}, pcs_missing_dir={stats.pcs_with_missing_dir}, "
                f"pcs_no_csv={stats.pcs_with_no_csv}"
            )
            self.done.emit(True, msg, [str(p) for p in cached])

        except Exception as e:
            self.done.emit(False, f"Error: {e}", [])