from __future__ import annotations

from pathlib import Path
from typing import List

from PyQt6.QtCore import QThread, pyqtSignal

from pc_config import PCEntry
from multi_pc_checker import check_all_pcs


class MultiPCCheckWorker(QThread):
    finished = pyqtSignal(list)     # List[PCCheckResult]
    failed = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, pcs: List[PCEntry], kickout_dir: Path, vision_mode: str):
        super().__init__()
        self._pcs = pcs
        self._kickout_dir = kickout_dir
        self._vision_mode = vision_mode

    def run(self):
        try:
            self.progress.emit(f"Checking {len(self._pcs)} PCs… ({self._vision_mode})")
            results = check_all_pcs(self._pcs, self._kickout_dir, self._vision_mode)
            self.finished.emit(results)
        except Exception as e:
            self.failed.emit(str(e))
