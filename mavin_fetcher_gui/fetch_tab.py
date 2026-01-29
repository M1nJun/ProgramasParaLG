from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox,
    QProgressBar, QMessageBox
)

from .log_widget import LogWidget
from .fetch_worker import FetchWorker, FetchTaskConfig
from .drive_selector import DriveSelectorWidget
from .session_panel import SessionPanel
from .session_manager import SessionManager


class FetchTab(QWidget):
    def __init__(self, session: SessionManager):
        super().__init__()

        self.session = session
        self.worker: FetchWorker | None = None

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Shared session panel
        self.session_panel = SessionPanel(self.session)
        root.addWidget(self.session_panel)

        # Drives selector (E/F/G)
        self.drive_selector = DriveSelectorWidget()
        root.addWidget(self.drive_selector)

        self.include_active = QCheckBox("Include ActiveMap")
        root.addWidget(self.include_active)

        # Buttons
        row = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        row.addWidget(self.run_btn)
        row.addWidget(self.cancel_btn)
        row.addStretch(1)
        root.addLayout(row)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        info_row = QHBoxLayout()
        self.progress_label = QLabel("Copied: 0 / 0")
        self.class_label = QLabel("Current class: -")
        self.file_label = QLabel("File: -")
        info_row.addWidget(self.progress_label)
        info_row.addSpacing(16)
        info_row.addWidget(self.class_label)
        info_row.addSpacing(16)
        info_row.addWidget(self.file_label)
        info_row.addStretch(1)
        root.addLayout(info_row)

        # Log
        root.addWidget(QLabel("Log:"))
        self.log = LogWidget()
        self.log.setMinimumHeight(220)
        root.addWidget(self.log)

        # signals
        self.run_btn.clicked.connect(self.on_run)
        self.cancel_btn.clicked.connect(self.on_cancel)

    def on_run(self) -> None:
        if self.worker and self.worker.isRunning():
            return

        s = self.session.state
        days = s.to_days()
        if not days:
            QMessageBox.warning(self, "Missing input", "Please select a valid date / range / dates in Session.")
            return

        drives_text = self.drive_selector.to_text()
        if not drives_text.strip():
            QMessageBox.warning(self, "Missing input", "Please select at least one drive (E/F/G).")
            return

        if not s.out_dir.strip():
            QMessageBox.warning(self, "Missing input", "Please choose an output folder in Session.")
            return

        cfg = FetchTaskConfig(
            date_mode=s.date_mode,
            date_text="",  # not used by worker when we pass state-derived fields? (kept for compatibility)
            out_dir=s.out_dir,
            model=s.model,
            drives_text=drives_text,
            include_activemap=self.include_active.isChecked(),
        )

        # Worker expects date_text; simplest: encode state into date_text used by worker parser:
        # We'll keep worker unchanged by providing what it expects:
        if s.date_mode == "Single date":
            cfg = FetchTaskConfig(s.date_mode, s.single_date, s.out_dir, s.model, drives_text, cfg.include_activemap)
        elif s.date_mode == "Date range":
            cfg = FetchTaskConfig(s.date_mode, f"{s.range_start} {s.range_end}", s.out_dir, s.model, drives_text, cfg.include_activemap)
        else:
            cfg = FetchTaskConfig(s.date_mode, ",".join(s.specific_dates or []), s.out_dir, s.model, drives_text, cfg.include_activemap)

        self.progress.setValue(0)
        self.progress_label.setText("Copied: 0 / 0")
        self.class_label.setText("Current class: -")
        self.file_label.setText("File: -")
        self.log.append_line("[INFO] Starting fetch...")

        self.worker = FetchWorker(cfg)
        self.worker.progress_pct.connect(self.progress.setValue)
        self.worker.log.connect(self.log.append_line)
        self.worker.status.connect(self.on_status)
        self.worker.done.connect(self.on_done)

        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.worker.start()

    def on_status(self, done: int, total: int, class_name: str, filename: str) -> None:
        self.progress_label.setText(f"Copied: {done} / {total}")
        self.class_label.setText(f"Current class: {class_name}")
        self.file_label.setText(f"File: {filename}")

    def on_cancel(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.cancel()

    def on_done(self, success: bool, message: str) -> None:
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        if success:
            QMessageBox.information(self, "Done", message)
        else:
            QMessageBox.warning(self, "Stopped", message)

    def apply_settings(self, s) -> None:
        # Only per-fetch settings here; session is handled by MainWindow->SessionManager
        self.drive_selector.from_text(getattr(s, "drives_text", "") or "")
        self.include_active.setChecked(bool(getattr(s, "include_activemap", False)))

    def collect_settings(self) -> dict:
        return {
            "drives_text": self.drive_selector.to_text(),
            "include_activemap": self.include_active.isChecked(),
        }
