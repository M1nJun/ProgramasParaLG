from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

from checker import CheckReport
from pc_config import PCEntry
from ui_report_viewer import ReportViewerWidget


class MultiDetailPane(QWidget):
    """
    Bottom pane for MultiPCWidget:
      - shows selected PC header
      - shows per-measure details via ReportViewerWidget
      - provides a button to open the full details dialog (re-check optional there)
    """
    def __init__(self, reports_dir: Path):
        super().__init__()
        self.reports_dir = reports_dir

        self._pc: Optional[PCEntry] = None
        self._report: Optional[CheckReport] = None

        self.title_label = QLabel("Select a PC row to see details.")
        self.viewer = ReportViewerWidget(reports_dir=self.reports_dir)

        self.open_dialog_btn = QPushButton("Open Details Dialog")
        self.open_dialog_btn.setEnabled(False)

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.open_dialog_btn)

        root.addLayout(header)
        root.addWidget(self.viewer)
        self.setLayout(root)

    def set_selection(self, pc: Optional[PCEntry], report: Optional[CheckReport], error: str = ""):
        self._pc = pc
        self._report = report

        if pc is None:
            self.title_label.setText("Select a PC row to see details.")
            self.viewer.set_report(None)
            self.open_dialog_btn.setEnabled(False)
            return

        if error:
            self.title_label.setText(f"{pc.key} ({pc.ip}) — ERROR: {error}")
            self.viewer.set_report(None)
            self.open_dialog_btn.setEnabled(True)
            return

        if report is None:
            self.title_label.setText(f"{pc.key} ({pc.ip}) — No cached report.")
            self.viewer.set_report(None)
            self.open_dialog_btn.setEnabled(True)
            return

        self.title_label.setText(f"{pc.key} ({pc.ip}) — Recipe: {report.recipe_name} / {report.recipe_id_3digit}")
        self.viewer.set_report(report)
        self.open_dialog_btn.setEnabled(True)