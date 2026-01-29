from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from mavin_fetcher.view_index import build_view_index, ViewIndex


@dataclass(frozen=True)
class ViewerBuildConfig:
    out_dir: str


class ViewerWorker(QThread):
    log = pyqtSignal(str)
    done = pyqtSignal(object)  # ViewIndex
    failed = pyqtSignal(str)

    def __init__(self, cfg: ViewerBuildConfig):
        super().__init__()
        self.cfg = cfg

    def run(self) -> None:
        try:
            out_dir = Path(self.cfg.out_dir).expanduser().resolve()
            self.log.emit(f"[INFO] Building viewer index from: {out_dir}")
            idx = build_view_index(out_dir)
            self.log.emit(f"[INFO] Classes found: {len(idx.classes)}")
            self.done.emit(idx)
        except Exception as e:
            self.failed.emit(f"Error: {e}")
