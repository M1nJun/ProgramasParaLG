from __future__ import annotations

import time
from dataclasses import dataclass

from PyQt6.QtCore import QThread, pyqtSignal


@dataclass(frozen=True)
class DummyTaskConfig:
    task_name: str = "Dummy Task"
    steps: int = 100
    delay_ms: int = 10


class DummyWorker(QThread):
    progress = pyqtSignal(int)      # 0..100
    log = pyqtSignal(str)
    done = pyqtSignal(bool, str)    # (success, message)

    def __init__(self, cfg: DummyTaskConfig):
        super().__init__()
        self.cfg = cfg
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        self.log.emit(f"[INFO] Starting: {self.cfg.task_name}")
        steps = max(1, int(self.cfg.steps))

        for i in range(steps + 1):
            if self._cancel:
                self.log.emit("[WARN] Cancelled by user.")
                self.done.emit(False, "Cancelled.")
                return

            pct = int(i * 100 / steps)
            self.progress.emit(pct)

            if i in (0, steps // 4, steps // 2, (steps * 3) // 4, steps):
                self.log.emit(f"[INFO] {self.cfg.task_name}: {pct}%")

            time.sleep(max(0, self.cfg.delay_ms) / 1000.0)

        self.log.emit(f"[INFO] Finished: {self.cfg.task_name}")
        self.done.emit(True, f"{self.cfg.task_name} completed.")
