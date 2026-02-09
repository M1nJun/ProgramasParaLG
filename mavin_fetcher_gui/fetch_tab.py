from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox,
    QProgressBar, QMessageBox, QApplication
)

from mavin_fetcher.area_spec import AreaSpec, AREA_B

from .log_widget import LogWidget
from .fetch_worker import FetchWorker, FetchTaskConfig
from .session_panel import SessionPanel
from .session_manager import SessionManager


class FetchTab(QWidget):
    def __init__(self, session: SessionManager, *, area: AreaSpec = AREA_B):
        super().__init__()

        self.session = session
        self.area = area
        self.worker: FetchWorker | None = None

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Session panel (area-aware)
        self.session_panel = SessionPanel(self.session, area=self.area)
        root.addWidget(self.session_panel)

        self.include_active = QCheckBox("Include ActiveMap")
        root.addWidget(self.include_active)

        # Buttons
        row = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)

        self.run_btn.setAutoDefault(False)
        self.run_btn.setDefault(False)
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.setDefault(False)

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

        cfg = FetchTaskConfig(
            date_mode=s.date_mode,
            date_text=date_text,
            out_dir=s.out_dir,
            model=s.model,
            selected_pcs=list(s.selected_pcs),
            include_activemap=self.include_active.isChecked(),
            # NOTE: we’ll wire this into the engine in the next step
            area_id=self.area.area_id,
        )

        self.progress.setValue(0)
        self.progress_label.setText("Copied: 0 / 0")
        self.class_label.setText("Current class: -")
        self.file_label.setText("File: -")
        self.log.append_line("[INFO] Starting remote fetch...")

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
        self.include_active.setChecked(bool(getattr(s, "include_activemap", False)))

    def collect_settings(self) -> dict:
        return {
            "include_activemap": self.include_active.isChecked(),
        }