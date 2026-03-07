"""
Main application window.

Responsibilities:
    - Create the top-level window with tab navigation.
    - Hold references to the Fetch and Review tabs.
    - Manage communication between tabs (fetch results -> review tab).
"""

import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QStatusBar,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette

from ui.fetch_tab import FetchTab
from ui.review_tab import ReviewTab
from ui.styles import apply_app_style


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bi-Hourly Image Reviewer")
        self.setMinimumSize(1200, 800)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Build the UI layout."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs)

        # Create tabs
        self.fetch_tab = FetchTab()
        self.review_tab = ReviewTab()

        self.tabs.addTab(self.fetch_tab, "  Fetch  ")
        self.tabs.addTab(self.review_tab, "  Review  ")

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _connect_signals(self):
        """Wire up cross-tab communication."""
        # When fetch completes, pass results to review tab and switch to it
        self.fetch_tab.fetch_complete.connect(self._on_fetch_complete)

    def _on_fetch_complete(self, results: dict):
        """Handle fetch completion: load results into review tab."""
        self.review_tab.load_results(results)
        self.tabs.setCurrentWidget(self.review_tab)
        self.status_bar.showMessage(
            f"Loaded {results.get('fetched', 0)} cells for review"
        )


def launch_app():
    """Application entry point."""
    app = QApplication(sys.argv)
    apply_app_style(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())