from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox

from pc_config import PCEntry
from workers import MultiPCCheckWorker
from ui_crash_log import append_crash_log


class PCDetailsDialog(QDialog):
    """
    IMPORTANT:
    - This class assumes your dialog already shows some kind of report viewer.
    - The crash fix is the worker lifecycle: keep self._recheck_worker alive + never touch UI from worker thread.
    """

    def __init__(
        self,
        pc: PCEntry,
        kickout_dir: Path,
        reports_dir: Path,
        vision_mode: str,
        parent=None,
    ):
        super().__init__(parent)

        self.pc = pc
        self.kickout_dir = kickout_dir
        self.reports_dir = reports_dir
        self.vision_mode = vision_mode

        self._recheck_worker: MultiPCCheckWorker | None = None

        self.setWindowTitle(f"PC Details — {pc.key} ({pc.ip})")
        self.resize(900, 650)

        self._build_ui()

        # Initial load (whatever you already do)
        # self._load_cached_or_run_once()

    def _build_ui(self) -> None:
        root = QVBoxLayout()
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        header = QLabel(f"{self.pc.key}  |  {self.pc.ip}  |  Vision: {self.vision_mode}")
        header.setStyleSheet("font-size: 16px; font-weight: 600;")
        root.addWidget(header)

        # Status line (used for progress text)
        self.status_label = QLabel("Ready.")
        root.addWidget(self.status_label)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.recheck_btn = QPushButton("Re-check this PC")
        self.recheck_btn.clicked.connect(self._on_recheck_clicked)
        btn_row.addWidget(self.recheck_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        root.addLayout(btn_row)

        # ---- Your existing report viewer widget goes here ----
        # Example:
        # root.addWidget(self.report_viewer)
        #
        # Keep your current UI; don’t change behavior/layout unless needed.

        self.setLayout(root)

    def _set_busy(self, busy: bool) -> None:
        self.recheck_btn.setEnabled(not busy)

    def _on_recheck_clicked(self) -> None:
        # Guard: prevent double-run (double-click or repeated presses)
        if self._recheck_worker and self._recheck_worker.isRunning():
            QMessageBox.information(self, "Busy", "Re-check is already running for this PC.")
            return

        try:
            self._set_busy(True)
            self.status_label.setText(f"Re-checking {self.pc.key}...")

            # KEY FIX:
            # Keep a strong reference on self so Qt doesn't GC the thread -> hard crash
            self._recheck_worker = MultiPCCheckWorker([self.pc], self.kickout_dir, self.vision_mode)

            # Safe: signals execute on UI thread
            self._recheck_worker.progress.connect(self.status_label.setText)
            self._recheck_worker.failed.connect(self._on_recheck_failed)
            self._recheck_worker.finished.connect(self._on_recheck_finished)

            self._recheck_worker.start()

        except Exception as e:
            append_crash_log(self.reports_dir, "PCDetailsDialog._on_recheck_clicked", e)
            self._set_busy(False)
            QMessageBox.critical(
                self,
                "Re-check crashed",
                "Re-check failed due to an internal error.\n"
                "See reports/ui_crash.log for details."
            )

    def _on_recheck_failed(self, msg: str) -> None:
        self._set_busy(False)
        self.status_label.setText("Re-check failed.")
        QMessageBox.critical(self, "Re-check Failed", msg)

        # Release the worker reference safely
        self._recheck_worker = None

    def _on_recheck_finished(self, results: list[Any]) -> None:
        try:
            self._set_busy(False)

            if not results:
                self.status_label.setText("Re-check finished (no result).")
                QMessageBox.warning(self, "Re-check", "No result returned for this PC.")
                self._recheck_worker = None
                return

            # MultiPCCheckWorker returns a list; for single PC we take first
            res = results[0]

            # Update your report UI here WITHOUT crashing:
            # - if your viewer expects (pc, report, error), set it accordingly
            # Example (adapt to your actual widgets):
            # if res.error:
            #     self.report_viewer.set_error(res.error)
            # else:
            #     self.report_viewer.set_report(res.report)

            if getattr(res, "error", ""):
                self.status_label.setText(f"Done: ERROR ({res.error})")
            else:
                self.status_label.setText("Done.")

            # Release worker reference
            self._recheck_worker = None

        except Exception as e:
            append_crash_log(self.reports_dir, "PCDetailsDialog._on_recheck_finished", e)
            self.status_label.setText("Re-check finished, but UI update failed. See reports/ui_crash.log.")
            QMessageBox.critical(
                self,
                "UI update crashed",
                "Re-check finished, but updating the UI crashed.\n"
                "See reports/ui_crash.log for details."
            )
            self._recheck_worker = None