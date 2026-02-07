from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from ui_multi import MultiPCWidget


class AppTabs(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bypass Checker")

        layout = QVBoxLayout()
        tabs = QTabWidget()

        # Single tab for now (expandable later)
        tabs.addTab(MultiPCWidget(), "All PCs")
        tabs.setCurrentIndex(0)

        layout.addWidget(tabs)
        self.setLayout(layout)
        self.resize(1300, 750)