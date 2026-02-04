from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
)

from pc_config import PCEntry
from multi_pc_checker import check_one_pc
from ui_report_viewer import ReportViewerWidget


class PCDetailsDialog(QDialog):
    def __init__(self, pc: PCEntry, kickout_dir: Path, reports_dir: Path, vision_mode: str, parent=None):
        super().__init__(parent)
        self.pc = pc
        self.kickout_dir = kickout_dir
        self.reports_dir = reports_dir
        self.vision_mode = vision_mode

        self.setWindowTitle(f"PC Details — {pc.key} ({pc.ip})")
        self.resize(1200, 720)

        self.viewer = ReportViewerWidget(reports_dir=self.reports_dir)

        self._build_ui()
        self.run_check()

    def _build_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(QLabel(
            f"Vision: {self.vision_mode}    PC: {self.pc.key}    IP: {self.pc.ip}    "
            f"Line: {self.pc.line}    Polarity: {self.pc.polarity}"
        ))

        header.addStretch()

        self.check_btn = QPushButton("Check This PC")
        self.check_btn.clicked.connect(self.run_check)
        header.addWidget(self.check_btn)

        root.addLayout(header)
        root.addWidget(self.viewer)

        self.setLayout(root)

    def run_check(self):
        res = check_one_pc(self.pc, self.kickout_dir, self.vision_mode)
        if res.error:
            QMessageBox.critical(self, "Check Failed", res.error)
            self.viewer.set_report(None)
            return
        self.viewer.set_report(res.report)
