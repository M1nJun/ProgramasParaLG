"""
Cell List Widget.

Responsibilities:
    - Display a scrollable list of defect cells.
    - Show cell ID, defect type, side, and judge badge per item.
    - Emit a signal when a cell is selected.
    - Support programmatic navigation (next/previous).
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QFont

from ui.styles import COLORS, JUDGE_COLORS, FONT_FAMILY_MONO, SPACING_SM, SPACING_MD


class CellItemWidget(QWidget):
    """
    Custom widget rendered inside each list item.
    Shows cell ID, defect type, side indicator, and judge badge.
    """

    def __init__(self, cell_data: dict, parent=None):
        super().__init__(parent)
        self.cell_data = cell_data
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_SM, SPACING_SM, SPACING_SM, SPACING_SM)
        layout.setSpacing(2)

        # Top row: cell ID + judge badge
        top_row = QHBoxLayout()
        top_row.setSpacing(SPACING_SM)

        cell_label = QLabel(self.cell_data.get("cell_id", "???"))
        cell_label.setFont(QFont(FONT_FAMILY_MONO, 10, QFont.Bold))
        cell_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        top_row.addWidget(cell_label)

        top_row.addStretch()

        # Judge badge
        judge = self.cell_data.get("judge", "")
        badge_color = JUDGE_COLORS.get(judge, COLORS["text_muted"])
        badge = QLabel(judge)
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedWidth(50)
        badge.setStyleSheet(
            f"background-color: {badge_color}; "
            f"color: white; "
            f"border-radius: 3px; "
            f"padding: 1px 6px; "
            f"font-size: 8pt; "
            f"font-weight: 700;"
        )
        top_row.addWidget(badge)

        layout.addLayout(top_row)

        # Bottom row: defect type + side
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(SPACING_SM)

        defect_label = QLabel(self.cell_data.get("judge_defect", ""))
        defect_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 9pt;"
        )
        bottom_row.addWidget(defect_label)

        bottom_row.addStretch()

        side = self.cell_data.get("side", "")
        side_text = {"UPPER": "▲ Upper", "LOWER": "▼ Lower", "BOTH": "◆ Both"}.get(
            side, side
        )
        side_label = QLabel(side_text)
        side_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 8pt;"
        )
        bottom_row.addWidget(side_label)

        layout.addLayout(bottom_row)


class CellListWidget(QWidget):
    """
    Scrollable list of defect cells.
    Emits cell_selected signal with the cell data dict when selection changes.
    """

    cell_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cells = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("  Defect Cells")
        header.setFixedHeight(36)
        header.setStyleSheet(
            f"background-color: {COLORS['bg_header']}; "
            f"color: {COLORS['text_secondary']}; "
            f"font-weight: 600; "
            f"font-size: 10pt; "
            f"padding-left: {SPACING_MD}px;"
        )
        layout.addWidget(header)

        # List
        self.list_widget = QListWidget()
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.setFocusPolicy(Qt.NoFocus)  # We handle keys in ReviewTab
        layout.addWidget(self.list_widget)

    def _connect_signals(self):
        self.list_widget.currentRowChanged.connect(self._on_row_changed)

    def load_cells(self, cell_results: list):
        """
        Populate the list with cell results from the fetch pipeline.

        Args:
            cell_results: List of dicts from fetch_pipeline results.
        """
        self.list_widget.clear()
        self._cells = cell_results

        for cell_data in cell_results:
            item = QListWidgetItem()
            widget = CellItemWidget(cell_data)
            item.setSizeHint(QSize(0, 56))
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

        # Select first item if available
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_row_changed(self, row: int):
        """Emit cell_selected when selection changes."""
        if 0 <= row < len(self._cells):
            self.cell_selected.emit(self._cells[row])

    def select_next(self):
        """Move selection to the next cell."""
        current = self.list_widget.currentRow()
        if current < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(current + 1)

    def select_previous(self):
        """Move selection to the previous cell."""
        current = self.list_widget.currentRow()
        if current > 0:
            self.list_widget.setCurrentRow(current - 1)

    def current_index(self) -> int:
        """Return the current selected row index."""
        return self.list_widget.currentRow()

    def cell_count(self) -> int:
        """Return total number of cells in the list."""
        return self.list_widget.count()