from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QThread

from .fs_ops import backup_source_into_dl_version, copy_overwrite_only, count_files


class InjectSignals(QObject):
    log = Signal(str)
    progress = Signal(int, int)  # current, total
    done = Signal(bool, str)     # success, message


@dataclass
class InjectJob:
    source_folder: Path
    target_model_folder: Path
    do_backup: bool = True


class InjectWorker(QThread):
    def __init__(self, job: InjectJob):
        super().__init__()
        self.job = job
        self.signals = InjectSignals()

    def _log(self, msg: str) -> None:
        self.signals.log.emit(msg)

    def run(self) -> None:
        try:
            src = self.job.source_folder
            dst = self.job.target_model_folder

            self._log(f"Source: {src}")
            self._log(f"Target: {dst}")

            total = count_files(src)
            if total == 0:
                self.signals.progress.emit(0, 0)
                raise RuntimeError("Source folder contains no files to copy.")

            self.signals.progress.emit(0, total)
            copied = 0

            def on_file(_s, _d):
                nonlocal copied
                copied += 1
                if copied % 5 == 0 or copied == total:
                    self.signals.progress.emit(copied, total)

            if self.job.do_backup:
                self._log("Creating backup in DL_VERSION ...")
                backup_dir = backup_source_into_dl_version(src, dst)
                self._log(f"Backup saved to: {backup_dir}")

            self._log("Copying (overwrite-only) into target model folder ...")
            copy_overwrite_only(src, dst, on_file_copied=on_file)

            self.signals.progress.emit(total, total)
            self.signals.done.emit(True, "Injection completed successfully.")
        except Exception as e:
            self.signals.done.emit(False, f"Injection failed: {e}")
