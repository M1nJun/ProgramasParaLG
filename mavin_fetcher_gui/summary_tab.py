from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox,
    QProgressBar, QMessageBox, QGroupBox
)

from mavin_fetcher.csv_autofind import find_csvs_for_days, flatten_paths

from .file_pickers import pick_files
from .log_widget import LogWidget
from .summary_worker import SummaryWorker, SummaryTaskConfig
from .summary_table_widget import SummaryTableWidget
from .session_panel import SessionPanel
from .session_manager import SessionManager


class SummaryTab(QWidget):
    # NEW: emitted when user double-clicks a class in the summary table (e.g., "NG_CRITICAL")
    class_selected = pyqtSignal(str)

    def __init__(self, session: SessionManager):
        super().__init__()

        self.session = session
        self.worker: SummaryWorker | None = None

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Shared session panel
        self.session_panel = SessionPanel(self.session)
        root.addWidget(self.session_panel)

        inputs_box = QGroupBox("Summary")
        form = QFormLayout(inputs_box)

        csv_row = QHBoxLayout()
        self.csv_paths = QLineEdit("")
        self.browse_csv = QPushButton("Browse…")
        self.auto_find = QPushButton("Auto-find from Session")
        csv_row.addWidget(self.csv_paths)
        csv_row.addWidget(self.browse_csv)
        csv_row.addWidget(self.auto_find)
        form.addRow("CSV file(s):", csv_row)

        self.top_n = QSpinBox()
        self.top_n.setRange(1, 200)
        self.top_n.setValue(20)
        form.addRow("Top N (text only):", self.top_n)

        root.addWidget(inputs_box)

        row = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        row.addWidget(self.run_btn)
        row.addStretch(1)
        root.addLayout(row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        self.progress_label = QLabel("Files: 0 / 0")
        root.addWidget(self.progress_label)

        root.addWidget(QLabel("Counts (by cell + by region):"))
        self.table = SummaryTableWidget()
        self.table.setMinimumHeight(260)
        root.addWidget(self.table)

        # NEW: forward class selection
        self.table.class_selected.connect(self.class_selected.emit)

        root.addWidget(QLabel("Raw text output:"))
        self.log = LogWidget()
        self.log.setMinimumHeight(220)
        root.addWidget(self.log)

        self.browse_csv.clicked.connect(self.on_browse)
        self.auto_find.clicked.connect(self.on_auto_find)
        self.run_btn.clicked.connect(self.on_run)

    def on_browse(self) -> None:
        picked = pick_files(self, "Select CSV/XLSX file(s)")
        if picked:
            self.csv_paths.setText(";".join(picked))

    def on_auto_find(self) -> None:
        s = self.session.state
        days = s.to_days()
        if not days:
            QMessageBox.warning(self, "Missing input", "Please select a valid date / range / dates in Session.")
            return

        csv_dir = Path(s.csv_dir).expanduser().resolve()
        if not csv_dir.exists():
            QMessageBox.warning(self, "Missing folder", f"CSV folder not found:\n{csv_dir}")
            return

        matches = find_csvs_for_days(csv_dir, s.model, days)
        paths = flatten_paths(matches)

        if not paths:
            QMessageBox.information(self, "No CSV found", "No CSV files matched the selected day(s)/model.")
            return

        self.csv_paths.setText(";".join(str(p) for p in paths))
        self.log.append_line(f"[INFO] Auto-found {len(paths)} CSV file(s) from Session.")

    def _get_paths_list(self) -> list[str]:
        raw = (self.csv_paths.text() or "").strip()
        if not raw:
            return []
        raw = raw.replace("\n", ";").replace(",", ";")
        return [p.strip() for p in raw.split(";") if p.strip()]

    def on_run(self) -> None:
        if self.worker and self.worker.isRunning():
            return

        paths = self._get_paths_list()
        if not paths:
            QMessageBox.warning(self, "Missing input", "Please choose at least one CSV/XLSX file.")
            return

        cfg = SummaryTaskConfig(csv_paths=paths, top_n=int(self.top_n.value()))

        self.progress.setValue(0)
        self.progress_label.setText("Files: 0 / 0")
        self.table.set_summary_data({})
        self.log.clear()
        self.log.append_line("[INFO] Starting summary...")

        self.worker = SummaryWorker(cfg)
        self.worker.progress_pct.connect(self.progress.setValue)
        self.worker.status.connect(self.on_status)
        self.worker.log.connect(self.log.append_line)
        self.worker.data.connect(self.on_data)
        self.worker.output.connect(self._show_output)
        self.worker.done.connect(self.on_done)

        self.run_btn.setEnabled(False)
        self.worker.start()

    def on_status(self, done: int, total: int) -> None:
        self.progress_label.setText(f"Files: {done} / {total}")

    def on_data(self, data: object) -> None:
        self.table.set_summary_data(data if isinstance(data, dict) else {})

    def _show_output(self, text: str) -> None:
        self.log.append_line("")
        self.log.append_line(text)

    def on_done(self, success: bool, message: str) -> None:
        self.run_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "Done", message)
        else:
            QMessageBox.warning(self, "Stopped", message)

    def apply_settings(self, s) -> None:
        if getattr(s, "summary_csv_paths", None):
            self.csv_paths.setText(";".join(s.summary_csv_paths))
        self.top_n.setValue(int(getattr(s, "summary_top_n", 20) or 20))

    def collect_settings(self) -> dict:
        return {
            "summary_csv_paths": self._get_paths_list(),
            "summary_top_n": int(self.top_n.value()),
        }
