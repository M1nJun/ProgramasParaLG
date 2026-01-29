from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from mavin_fetcher.engine_summary import summarize_files


@dataclass(frozen=True)
class SummaryTaskConfig:
    csv_paths: list[str]
    top_n: int


class SummaryWorker(QThread):
    progress_pct = pyqtSignal(int)     # 0..100
    status = pyqtSignal(int, int)      # done, total
    log = pyqtSignal(str)
    output = pyqtSignal(str)           # text fallback
    data = pyqtSignal(object)          # NEW: structured payload
    done = pyqtSignal(bool, str)

    def __init__(self, cfg: SummaryTaskConfig):
        super().__init__()
        self.cfg = cfg

    def run(self) -> None:
        try:
            paths = [Path(p).expanduser().resolve() for p in (self.cfg.csv_paths or [])]
            top_n = int(self.cfg.top_n)

            def on_progress(done: int, total: int) -> None:
                if total <= 0:
                    self.progress_pct.emit(0)
                    self.status.emit(0, 0)
                    return
                self.progress_pct.emit(int(done * 100 / total))
                self.status.emit(done, total)

            res = summarize_files(
                paths=paths,
                top_n=top_n,
                log=self.log.emit,
                progress=on_progress,
            )

            self.data.emit(res.data)
            self.output.emit(res.text)
            self.done.emit(True, f"Done. Summarized {res.file_count} file(s).")

        except Exception as e:
            self.done.emit(False, f"Error: {e}")
