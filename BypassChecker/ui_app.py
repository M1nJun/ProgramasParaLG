from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from ui_single import SinglePCWidget
from ui_multi import MultiPCWidget


class AppTabs(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bypass Checker")

        layout = QVBoxLayout()
        tabs = QTabWidget()

        # All PCs tab first (left) + default selected
        tabs.addTab(MultiPCWidget(), "All PCs")
        tabs.addTab(SinglePCWidget(), "This PC")
        tabs.setCurrentIndex(0)

        layout.addWidget(tabs)
        self.setLayout(layout)
        self.resize(1300, 750)
