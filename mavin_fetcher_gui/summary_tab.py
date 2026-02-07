from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox,
    QProgressBar, QMessageBox, QGroupBox, QTabWidget
)

from mavin_fetcher.csv_autofind import find_csvs_for_days, flatten_paths

from .file_pickers import pick_files
from .log_widget import LogWidget
from .summary_worker import SummaryWorker, SummaryTaskConfig
from .summary_table_widget import SummaryTableWidget
from .breakdown_table_widget import BreakdownTableWidget
from .summary_remote_csv_worker import RemoteCsvFetchWorker, RemoteCsvFetchConfig
from .session_panel import SessionPanel
from .session_manager import SessionManager


class SummaryTab(QWidget):
    class_selected = pyqtSignal(str)

    def __init__(self, session: SessionManager):
        super().__init__()

        self.session = session
        self.worker: SummaryWorker | None = None
        self.csv_fetcher: RemoteCsvFetchWorker | None = None

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.session_panel = SessionPanel(self.session)
        root.addWidget(self.session_panel)

        inputs_box = QGroupBox("Summary")
        form = QFormLayout(inputs_box)

        csv_row = QHBoxLayout()
        self.csv_paths = QLineEdit("")
        self.browse_csv = QPushButton("Browse…")
        self.auto_find = QPushButton("Auto-find from Session")
        self.fetch_remote = QPushButton("Fetch from Selected PCs")
        csv_row.addWidget(self.csv_paths)
        csv_row.addWidget(self.browse_csv)
        csv_row.addWidget(self.auto_find)
        csv_row.addWidget(self.fetch_remote)
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

        root.addWidget(QLabel("Summary tables:"))
        self.tabs = QTabWidget()

        # Overall
        overall_tab = QWidget()
        overall_layout = QVBoxLayout(overall_tab)
        self.table_overall = SummaryTableWidget()
        self.table_overall.setMinimumHeight(260)
        overall_layout.addWidget(self.table_overall)
        self.tabs.addTab(overall_tab, "Overall (Classes)")

        # By Line
        line_tab = QWidget()
        line_layout = QVBoxLayout(line_tab)
        self.table_by_line = BreakdownTableWidget()
        line_layout.addWidget(self.table_by_line)
        self.tabs.addTab(line_tab, "By Line")

        # By PC
        pc_tab = QWidget()
        pc_layout = QVBoxLayout(pc_tab)
        self.table_by_pc = BreakdownTableWidget()
        pc_layout.addWidget(self.table_by_pc)
        self.tabs.addTab(pc_tab, "By PC")

        root.addWidget(self.tabs)

        self.table_overall.class_selected.connect(self.class_selected.emit)

        root.addWidget(QLabel("Raw text output:"))
        self.log = LogWidget()
        self.log.setMinimumHeight(220)
        root.addWidget(self.log)

        self.browse_csv.clicked.connect(self.on_browse)
        self.auto_find.clicked.connect(self.on_auto_find)
        self.fetch_remote.clicked.connect(self.on_fetch_remote)
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

    def on_fetch_remote(self) -> None:
        if self.csv_fetcher and self.csv_fetcher.isRunning():
            return

        s = self.session.state
        days = s.to_days()
        if not days:
            QMessageBox.warning(self, "Missing input", "Please select a valid date / range / dates in Session.")
            return
        if not s.out_dir:
            QMessageBox.warning(self, "Missing output", "Session out_dir is not set. Please set an output folder.")
            return
        if not s.selected_pcs:
            QMessageBox.warning(self, "Missing PCs", "No PCs selected in Session.")
            return

        cfg = RemoteCsvFetchConfig(
            out_dir=Path(s.out_dir).expanduser().resolve(),
            model=s.model,
            days=days,
            selected_pc_keys=list(s.selected_pcs),
        )

        self.log.append_line("[INFO] Fetching CSVs from selected PCs into cache...")
        self.progress.setValue(0)
        self.progress_label.setText("Fetch steps: 0 / 0")
        self.fetch_remote.setEnabled(False)
        self.run_btn.setEnabled(False)

        self.csv_fetcher = RemoteCsvFetchWorker(cfg)
        self.csv_fetcher.log.connect(self.log.append_line)
        self.csv_fetcher.progress.connect(lambda d, t: self.progress_label.setText(f"Fetch steps: {d} / {t}"))
        self.csv_fetcher.progress_pct.connect(self.progress.setValue)
        self.csv_fetcher.done.connect(self.on_fetch_remote_done)
        self.csv_fetcher.start()

    def on_fetch_remote_done(self, success: bool, message: str, cached_paths_obj: object) -> None:
        self.fetch_remote.setEnabled(True)
        self.run_btn.setEnabled(True)

        cached_paths = cached_paths_obj if isinstance(cached_paths_obj, list) else []

        if success:
            self.log.append_line(f"[INFO] {message}")
            if cached_paths:
                self.csv_paths.setText(";".join(cached_paths))
                self.log.append_line(f"[INFO] Loaded {len(cached_paths)} cached CSV path(s) into Summary.")
            QMessageBox.information(self, "CSV Fetch Done", message)
        else:
            self.log.append_line(f"[WARN] {message}")
            QMessageBox.warning(self, "CSV Fetch Stopped", message)

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
        self.table_overall.set_summary_data({})
        self.table_by_line.set_groups({})
        self.table_by_pc.set_groups({})
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
        if not isinstance(data, dict):
            self.table_overall.set_summary_data({})
            self.table_by_line.set_groups({})
            self.table_by_pc.set_groups({})
            return

        self.table_overall.set_summary_data(data)
        self.table_by_line.set_groups(data.get("by_line", {}) or {})
        self.table_by_pc.set_groups(data.get("by_pc", {}) or {})

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