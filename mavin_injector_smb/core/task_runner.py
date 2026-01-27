from __future__ import annotations

import socket
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from .fs_ops import (
    backup_source_into_dl_version,
    copy_overwrite_only,
    count_files,
    ensure_dir,
    get_remote_mavin_root,
    list_relative_files,
    scan_models_canonical,
)

CONTROLLER_HOSTNAME = socket.gethostname()


class PcTaskSignals(QObject):
    log = Signal(str, str)               # pc_key, message
    status = Signal(str, str, str)       # pc_key, status, detail
    progress = Signal(str, int, int)     # pc_key, current, total
    finished = Signal(str, bool, str)    # pc_key, success, message


@dataclass(frozen=True)
class PcTask:
    pc_key: str
    ip: str
    model_canonical: str
    source_folder: Path
    do_backup: bool
    dry_run: bool


class PcRunnable(QRunnable):
    def __init__(self, task: PcTask, model_map: Dict[str, Path]):
        super().__init__()
        self.task = task
        self.model_map = model_map
        self.signals = PcTaskSignals()

    def _emit_status(self, st: str, detail: str = "") -> None:
        self.signals.status.emit(self.task.pc_key, st, detail)

    def _emit_log(self, msg: str) -> None:
        self.signals.log.emit(self.task.pc_key, msg)

    def run(self) -> None:
        try:
            src = Path(self.task.source_folder)
            total = count_files(src)
            if total == 0:
                raise RuntimeError("Source folder contains no files.")

            target_model = self.model_map.get(self.task.model_canonical)
            if not target_model:
                self._emit_status("SKIPPED", "Model folder not found on this PC")
                self.signals.finished.emit(self.task.pc_key, True, "Skipped (model not found).")
                return

            self._emit_status("RUNNING", "Preparing...")
            self._emit_log(f"Target model folder: {target_model}")

            dl_version = target_model / "DL_VERSION"
            ensure_dir(dl_version)

            if self.task.dry_run:
                self._emit_status("DRY RUN", "Writing marker...")
                rel_files = list_relative_files(src)
                ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                marker = dl_version / f"_INJECT_DRY_RUN_{ts}.txt"
                backup_target = dl_version / src.name

                lines = []
                lines.append("MAVIN Model Injector - DRY RUN (NO FILES COPIED)")
                lines.append(f"Timestamp: {ts}")
                lines.append(f"Controller PC: {CONTROLLER_HOSTNAME}")
                lines.append(f"PC: {self.task.pc_key} ({self.task.ip})")
                lines.append("")
                lines.append(f"Source folder: {src}")
                lines.append(f"Target model folder: {target_model}")
                lines.append("")
                lines.append("Backup (planned):")
                lines.append(f"  {backup_target}  (if exists, would use _1, _2, ...)")
                lines.append("")
                lines.append("Files that WOULD be copied/overwritten into target (relative paths):")
                lines.extend([f"  {p}" for p in rel_files])

                marker.write_text("\n".join(lines), encoding="utf-8")
                self._emit_status("DONE", f"Marker written: {marker.name}")
                self.signals.finished.emit(self.task.pc_key, True, f"Dry run marker written: {marker}")
                return

            copied = 0
            self.signals.progress.emit(self.task.pc_key, 0, total)

            def on_file(_s, _d):
                nonlocal copied
                copied += 1
                if copied % 10 == 0 or copied == total:
                    self.signals.progress.emit(self.task.pc_key, copied, total)

            if self.task.do_backup:
                self._emit_status("RUNNING", "Backing up...")
                backup_dir = backup_source_into_dl_version(src, target_model)
                self._emit_log(f"Backup saved to: {backup_dir}")

            self._emit_status("RUNNING", "Copying...")
            copy_overwrite_only(src, target_model, on_file_copied=on_file)

            self.signals.progress.emit(self.task.pc_key, total, total)
            self._emit_status("SUCCESS", "Completed")
            self.signals.finished.emit(self.task.pc_key, True, "Injection completed.")
        except Exception as e:
            self._emit_status("FAILED", str(e))
            self.signals.finished.emit(self.task.pc_key, False, str(e))


class TaskRunner(QObject):
    def __init__(self, max_concurrency: int = 4):
        super().__init__()
        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(max_concurrency)

    def scan_models_for_pc(self, ip: str) -> Dict[str, Path]:
        mavin = get_remote_mavin_root(ip)
        return scan_models_canonical(mavin)

    def start_task(self, task: PcTask, model_map: Dict[str, Path], *, connect):
        r = PcRunnable(task, model_map)
        connect(r)
        self.pool.start(r)
