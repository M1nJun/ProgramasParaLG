"""
Review Tab.

Responsibilities:
    - Display a list of fetched defect cells on the left.
    - Display images for the selected cell on the right.
    - Handle cell selection and keyboard navigation.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QLabel,
    QSizePolicy,
)
from PyQt5.QtCore import Qt

from ui.widgets.cell_list import CellListWidget
from ui.widgets.image_viewer import ImageViewer
from ui.styles import COLORS, SPACING_MD, SPACING_LG, SPACING_XL


class ReviewTab(QWidget):
    """Review tab with cell list and image viewer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Build the review tab layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Summary bar at top
        self.summary_bar = QWidget()
        self.summary_bar.setFixedHeight(44)
        self.summary_bar.setStyleSheet(
            f"background-color: {COLORS['bg_header']}; "
            f"padding: 0 {SPACING_LG}px;"
        )
        summary_layout = QHBoxLayout(self.summary_bar)
        summary_layout.setContentsMargins(SPACING_LG, 0, SPACING_LG, 0)

        self.summary_label = QLabel("No data loaded — run a fetch first")
        self.summary_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 10pt;"
        )
        summary_layout.addWidget(self.summary_label)
        summary_layout.addStretch()

        self.counter_label = QLabel("")
        self.counter_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 9pt;"
        )
        summary_layout.addWidget(self.counter_label)

        layout.addWidget(self.summary_bar)

        # Splitter: cell list (left) | image viewer (right)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(2)

        # Left panel — cell list
        self.cell_list = CellListWidget()
        self.cell_list.setMinimumWidth(280)
        self.cell_list.setMaximumWidth(450)
        self.splitter.addWidget(self.cell_list)

        # Right panel — image viewer
        self.image_viewer = ImageViewer()
        self.splitter.addWidget(self.image_viewer)

        # Set initial splitter sizes (30% list, 70% viewer)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([320, 880])

        layout.addWidget(self.splitter)

    def _connect_signals(self):
        """Wire up cell selection to image display."""
        self.cell_list.cell_selected.connect(self._on_cell_selected)

    def load_results(self, results: dict):
        """
        Load fetch results into the review tab.

        Args:
            results: Dict from fetch_pipeline.run_fetch().
        """
        self._results = results
        cell_results = results.get("results", [])

        # Update summary
        fetched = results.get("fetched", 0)
        failed = results.get("failed", 0)
        total = results.get("total_defects", 0)
        start = results.get("start_dt")
        end = results.get("end_dt")

        time_range = ""
        if start and end:
            time_range = (
                f"{start.strftime('%Y-%m-%d %H:%M')} → "
                f"{end.strftime('%Y-%m-%d %H:%M')}"
            )

        self.summary_label.setText(
            f"{time_range}    |    "
            f"{fetched} cells fetched, {failed} failed"
        )

        # Populate cell list
        self.cell_list.load_cells(cell_results)

        # Clear image viewer
        self.image_viewer.clear()
        self._update_counter()

    def _on_cell_selected(self, cell_data: dict):
        """Handle cell selection from the list."""
        output_dir = cell_data.get("output_dir", "")
        side = cell_data.get("side", "")
        cell_id = cell_data.get("cell_id", "")
        judge_defect = cell_data.get("judge_defect", "")

        self.image_viewer.load_images_from_directory(output_dir)
        self.image_viewer.set_cell_info(cell_id, judge_defect, side)
        self._update_counter()

    def _update_counter(self):
        """Update the cell counter in the summary bar."""
        current = self.cell_list.current_index()
        total = self.cell_list.cell_count()
        if total > 0:
            self.counter_label.setText(f"Cell {current + 1} of {total}")
        else:
            self.counter_label.setText("")

    def keyPressEvent(self, event):
        """
        Handle keyboard navigation.
        Up/Down arrows move between cells.
        Left/Right arrows move between images (handled by image_viewer).
        """
        key = event.key()
        if key == Qt.Key_Up:
            self.cell_list.select_previous()
            self._update_counter()
        elif key == Qt.Key_Down:
            self.cell_list.select_next()
            self._update_counter()
        elif key in (Qt.Key_Left, Qt.Key_Right):
            self.image_viewer.keyPressEvent(event)
        else:
            super().keyPressEvent(event)