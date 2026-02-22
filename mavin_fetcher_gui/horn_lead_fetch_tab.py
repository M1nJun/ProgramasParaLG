from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton,
    QProgressBar, QMessageBox, QApplication
)

from .log_widget import LogWidget
from .horn_lead_fetch_worker import HornLeadFetchWorker, HornLeadFetchTaskConfig
from .horn_lead_session_panel import HornLeadSessionPanel
from .session_manager import SessionManager

class HornLeadFetchTab(QWidget):
    def __init__(self, session: SessionManager):
        super().__init__()
        self.session = session
        self.worker: HornLeadFetchWorker | None = None

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.session_panel = HornLeadSessionPanel(self.session)
        root.addWidget(self.session_panel)

        row = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.run_btn.setAutoDefault(False)
        self.cancel_btn.setAutoDefault(False)

        row.addWidget(self.run_btn)
        row.addWidget(self.cancel_btn)
        row.addStretch(1)
        root.addLayout(row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        info_row = QHBoxLayout()
        self.progress_label = QLabel("Copied: 0 / 0")
        self.stage_label = QLabel("Stage: -")
        info_row.addWidget(self.progress_label)
        info_row.addSpacing(16)
        info_row.addWidget(self.stage_label)
        info_row.addStretch(1)
        root.addLayout(info_row)

        root.addWidget(QLabel("Log:"))
        self.log = LogWidget()
        self.log.setMinimumHeight(220)
        root.addWidget(self.log)

        self.run_btn.clicked.connect(self.on_run)
        self.cancel_btn.clicked.connect(self.on_cancel)

    def on_run(self) -> None:
        w = self.window()
        if not (w and w.isVisible() and QApplication.activeWindow() is w):
            return

        if self.worker and self.worker.isRunning():
            return

        s = self.session.state
        days = s.to_days()
        if not days:
            QMessageBox.warning(self, "Missing input", "Please select a valid date / range / dates in Session.")
            return
        if not s.selected_pcs:
            QMessageBox.warning(self, "Missing input", "Please select at least one PC in Session.")
            return
        if not s.out_dir.strip():
            QMessageBox.warning(self, "Missing input", "Please choose an output folder in Session.")
            return

        if s.date_mode == "Single date":
            date_text = s.single_date
        elif s.date_mode == "Date range":
            date_text = f"{s.range_start} {s.range_end}"
        else:
            date_text = ",".join(s.specific_dates or [])

        cfg = HornLeadFetchTaskConfig(
            date_mode=s.date_mode,
            date_text=date_text,
            out_dir=s.out_dir,
            model=s.model,
            csv_dir=s.csv_dir,
            selected_pcs=list(s.selected_pcs),
        )

        self.progress.setValue(0)
        self.progress_label.setText("Copied: 0 / 0")
        self.stage_label.setText("Stage: -")
        self.log.append_line("[INFO] Starting HORN LEAD remote fetch...")

        self.worker = HornLeadFetchWorker(cfg)
        self.worker.progress_pct.connect(self.progress.setValue)
        self.worker.log.connect(self.log.append_line)
        self.worker.status.connect(self.on_status)
        self.worker.done.connect(self.on_done)

        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.worker.start()

    def on_status(self, done: int, total: int, stage: str, _file: str) -> None:
        self.progress_label.setText(f"Copied: {done} / {total}")
        self.stage_label.setText(f"Stage: {stage}")

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