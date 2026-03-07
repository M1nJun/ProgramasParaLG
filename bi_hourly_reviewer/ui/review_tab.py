"""
Review Tab.

Responsibilities:
    - Display a list of fetched defect cells on the left.
    - Display images for the selected cell on the right.
    - Handle cell selection and keyboard navigation.
    - Filter cells by JUDGE type (NG, DLNG, C-NG).
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QLabel,
    QPushButton,
    QSizePolicy,
)
from PyQt5.QtCore import Qt

from ui.widgets.cell_list import CellListWidget
from ui.widgets.image_viewer import ImageViewer
from ui.styles import COLORS, JUDGE_COLORS, SPACING_MD, SPACING_LG, SPACING_XL


class JudgeFilterButton(QPushButton):
    """
    Toggle button for filtering by a specific JUDGE type.
    Shows the judge label and count, changes appearance when active.
    """

    def __init__(self, judge_type: str, parent=None):
        super().__init__(parent)
        self.judge_type = judge_type
        self._active = False
        self._count = 0
        self._color = JUDGE_COLORS.get(judge_type, COLORS["text_muted"])
        self.setFixedHeight(26)
        self.setFocusPolicy(Qt.NoFocus)  # Never steal focus from ReviewTab
        self._update_style()
        self._update_text()

    def set_count(self, count: int):
        self._count = count
        self._update_text()

    def set_active(self, active: bool):
        self._active = active
        self._update_style()

    def _update_text(self):
        self.setText(f" {self.judge_type}  ({self._count}) ")

    def _update_style(self):
        if self._active:
            self.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: {self._color};"
                f"  color: white;"
                f"  border: none;"
                f"  border-radius: 3px;"
                f"  padding: 2px 10px;"
                f"  font-size: 9pt;"
                f"  font-weight: 700;"
                f"}}"
                f"QPushButton:hover {{"
                f"  background-color: {self._color};"
                f"}}"
            )
        else:
            self.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: transparent;"
                f"  color: {self._color};"
                f"  border: 1px solid {self._color};"
                f"  border-radius: 3px;"
                f"  padding: 2px 10px;"
                f"  font-size: 9pt;"
                f"  font-weight: 600;"
                f"}}"
                f"QPushButton:hover {{"
                f"  background-color: {COLORS['bg_tertiary']};"
                f"}}"
            )


class ReviewTab(QWidget):
    """Review tab with cell list, image viewer, and judge filter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = None
        self._filter_buttons = {}
        self.setFocusPolicy(Qt.StrongFocus)  # Ensure we can receive key events
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
            f"background-color: {COLORS['bg_header']};"
        )
        summary_layout = QHBoxLayout(self.summary_bar)
        summary_layout.setContentsMargins(SPACING_LG, 0, SPACING_LG, 0)
        summary_layout.setSpacing(SPACING_MD)

        self.summary_label = QLabel("No data loaded — run a fetch first")
        self.summary_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 10pt;"
        )
        summary_layout.addWidget(self.summary_label)

        summary_layout.addStretch()

        # Filter buttons
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 9pt;"
        )
        summary_layout.addWidget(filter_label)

        for judge_type in ["NG", "DLNG", "C-NG"]:
            btn = JudgeFilterButton(judge_type)
            btn.clicked.connect(lambda _, jt=judge_type: self._on_filter_clicked(jt))
            self._filter_buttons[judge_type] = btn
            summary_layout.addWidget(btn)

        # "All" button
        self.all_btn = QPushButton("All")
        self.all_btn.setFixedHeight(26)
        self.all_btn.setFocusPolicy(Qt.NoFocus)  # Never steal focus
        self.all_btn.clicked.connect(self._on_all_clicked)
        self._update_all_btn_style(True)
        summary_layout.addWidget(self.all_btn)

        # Counter
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

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([320, 880])

        layout.addWidget(self.splitter)

        # Hotkey instructions bar at bottom
        hotkey_bar = QWidget()
        hotkey_bar.setFixedHeight(32)
        hotkey_bar.setStyleSheet(
            f"background-color: {COLORS['bg_header']};"
        )
        hotkey_layout = QHBoxLayout(hotkey_bar)
        hotkey_layout.setContentsMargins(SPACING_LG, 0, SPACING_LG, 0)

        hotkey_label = QLabel(
            "▲ ▼  Navigate cells        "
            "◀ ▶  Navigate images"
        )
        hotkey_label.setStyleSheet(
            f"color: {COLORS['accent_blue']}; font-size: 9pt; font-weight: 600;"
        )
        hotkey_layout.addWidget(hotkey_label)
        hotkey_layout.addStretch()

        layout.addWidget(hotkey_bar)

    def _connect_signals(self):
        """Wire up cell selection to image display."""
        self.cell_list.cell_selected.connect(self._on_cell_selected)

    def load_results(self, results: dict):
        """Load fetch results into the review tab."""
        self._results = results
        cell_results = results.get("results", [])

        # Update summary
        fetched = results.get("fetched", 0)
        failed = results.get("failed", 0)
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
            f"{fetched} fetched, {failed} failed"
        )

        # Reset filter to "All"
        self._set_active_filter(None)

        # Populate cell list
        self.cell_list.load_cells(cell_results)

        # Update filter counts
        self._update_filter_counts()

        # Clear image viewer
        self.image_viewer.clear()
        self._update_counter()

        # Grab focus so arrow keys work immediately
        self.setFocus()

    def _on_filter_clicked(self, judge_type: str):
        """Handle a judge filter button click."""
        current_filter = self.cell_list.get_filter()
        if current_filter == judge_type:
            self._set_active_filter(None)
        else:
            self._set_active_filter(judge_type)

        self.image_viewer.clear()
        self._update_counter()
        self.setFocus()  # Return focus for arrow keys

    def _on_all_clicked(self):
        """Handle the All button click."""
        self._set_active_filter(None)
        self.image_viewer.clear()
        self._update_counter()
        self.setFocus()  # Return focus for arrow keys

    def _set_active_filter(self, judge_type: str = None):
        """Update the filter state across buttons and cell list."""
        self.cell_list.set_filter(judge_type)

        for jt, btn in self._filter_buttons.items():
            btn.set_active(jt == judge_type)

        is_all = judge_type is None
        self._update_all_btn_style(is_all)

    def _update_all_btn_style(self, active: bool):
        if active:
            self.all_btn.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: {COLORS['accent_blue']};"
                f"  color: white;"
                f"  border: none;"
                f"  border-radius: 3px;"
                f"  padding: 2px 10px;"
                f"  font-size: 9pt;"
                f"  font-weight: 700;"
                f"}}"
            )
        else:
            self.all_btn.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: transparent;"
                f"  color: {COLORS['text_secondary']};"
                f"  border: 1px solid {COLORS['border']};"
                f"  border-radius: 3px;"
                f"  padding: 2px 10px;"
                f"  font-size: 9pt;"
                f"  font-weight: 600;"
                f"}}"
                f"QPushButton:hover {{"
                f"  background-color: {COLORS['bg_tertiary']};"
                f"}}"
            )

    def _update_filter_counts(self):
        counts = self.cell_list.get_judge_counts()
        for jt, btn in self._filter_buttons.items():
            btn.set_count(counts.get(jt, 0))

    def _on_cell_selected(self, cell_data: dict):
        output_dir = cell_data.get("output_dir", "")
        side = cell_data.get("side", "")
        cell_id = cell_data.get("cell_id", "")
        judge_defect = cell_data.get("judge_defect", "")

        self.image_viewer.load_images_from_directory(output_dir)
        self.image_viewer.set_cell_info(cell_id, judge_defect, side)
        self._update_counter()

    def _update_counter(self):
        current = self.cell_list.current_index()
        total = self.cell_list.cell_count()
        if total > 0:
            self.counter_label.setText(f"{current + 1} / {total}")
        else:
            self.counter_label.setText("0 / 0")

    def keyPressEvent(self, event):
        """Arrow keys: Up/Down for cells, Left/Right for images."""
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

    def mousePressEvent(self, event):
        """Grab focus back when clicking anywhere on the tab."""
        super().mousePressEvent(event)
        self.setFocus()