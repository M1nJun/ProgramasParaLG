"""
Cell List Widget.

Responsibilities:
    - Display a scrollable list of defect cells.
    - Show cell ID, defect type, side, and judge badge per item.
    - Emit a signal when a cell is selected.
    - Support programmatic navigation (next/previous).
    - Support filtering by JUDGE type (NG, DLNG, C-NG).

Uses a custom QStyledItemDelegate for fast rendering instead of
embedded QWidgets (which are slow to create in large numbers).
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QRect, QModelIndex
from PyQt5.QtGui import QFont, QPainter, QColor, QFontMetrics, QPen

from ui.styles import COLORS, JUDGE_COLORS, FONT_FAMILY_MONO, FONT_FAMILY, SPACING_SM, SPACING_MD


# Custom data roles for storing cell info on each QListWidgetItem
ROLE_CELL_ID = Qt.UserRole + 1
ROLE_JUDGE = Qt.UserRole + 2
ROLE_JUDGE_DEFECT = Qt.UserRole + 3
ROLE_SIDE = Qt.UserRole + 4
ROLE_DATA_INDEX = Qt.UserRole + 5  # index into _filtered_cells


class CellItemDelegate(QStyledItemDelegate):
    """
    Custom delegate that paints cell items directly.
    Much faster than creating QWidget per item.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._font_id = QFont(FONT_FAMILY_MONO, 10, QFont.Bold)
        self._font_defect = QFont(FONT_FAMILY, 9)
        self._font_badge = QFont(FONT_FAMILY, 8, QFont.Bold)
        self._font_side = QFont(FONT_FAMILY, 8)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(0, 52)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = option.rect
        is_selected = option.state & 0x00000004  # QStyle.State_Selected

        # Background
        if is_selected:
            painter.fillRect(rect, QColor(COLORS["bg_tertiary"]))
        else:
            painter.fillRect(rect, QColor(COLORS["bg_secondary"]))

        # Bottom border
        painter.setPen(QPen(QColor(COLORS["border"]), 1))
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

        # Data
        cell_id = index.data(ROLE_CELL_ID) or "???"
        judge = index.data(ROLE_JUDGE) or ""
        judge_defect = index.data(ROLE_JUDGE_DEFECT) or ""
        side = index.data(ROLE_SIDE) or ""

        pad = SPACING_SM
        x = rect.left() + pad + 4
        y_top = rect.top() + pad + 2

        # Top row: Cell ID (left) + Judge badge (right)
        # Cell ID
        painter.setFont(self._font_id)
        painter.setPen(QColor(COLORS["text_primary"]))
        painter.drawText(x, y_top + 14, cell_id)

        # Judge badge
        badge_color = QColor(JUDGE_COLORS.get(judge, COLORS["text_muted"]))
        badge_w = 48
        badge_h = 18
        badge_x = rect.right() - badge_w - pad - 4
        badge_y = y_top
        badge_rect = QRect(badge_x, badge_y, badge_w, badge_h)
        painter.setPen(Qt.NoPen)
        painter.setBrush(badge_color)
        painter.drawRoundedRect(badge_rect, 3, 3)
        painter.setFont(self._font_badge)
        painter.setPen(QColor("white"))
        painter.drawText(badge_rect, Qt.AlignCenter, judge)

        # Bottom row: Defect type (left) + Side (right)
        y_bottom = y_top + 24

        painter.setFont(self._font_defect)
        painter.setPen(QColor(COLORS["text_secondary"]))
        painter.drawText(x, y_bottom + 12, judge_defect)

        side_text = {"UPPER": "▲ Upper", "LOWER": "▼ Lower", "BOTH": "◆ Both"}.get(side, side)
        painter.setFont(self._font_side)
        painter.setPen(QColor(COLORS["text_muted"]))
        fm = QFontMetrics(self._font_side)
        side_w = fm.horizontalAdvance(side_text)
        painter.drawText(rect.right() - side_w - pad - 4, y_bottom + 12, side_text)

        painter.restore()


class CellListWidget(QWidget):
    """
    Scrollable list of defect cells with filtering support.
    Emits cell_selected signal with the cell data dict when selection changes.
    """

    cell_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_cells = []
        self._filtered_cells = []
        self._active_filter = None
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

        # List with custom delegate
        self.list_widget = QListWidget()
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.setItemDelegate(CellItemDelegate(self.list_widget))
        layout.addWidget(self.list_widget)

    def _connect_signals(self):
        self.list_widget.currentRowChanged.connect(self._on_row_changed)

    def load_cells(self, cell_results: list):
        """Load all cell results. Applies current filter automatically."""
        self._all_cells = cell_results
        self._apply_filter()

    def set_filter(self, judge_type: str = None):
        """Set the active JUDGE filter. None = show all."""
        self._active_filter = judge_type
        self._apply_filter()

    def get_filter(self) -> str:
        """Return the currently active filter, or None."""
        return self._active_filter

    def _apply_filter(self):
        """Re-populate the list based on the active filter."""
        if self._active_filter:
            self._filtered_cells = [
                c for c in self._all_cells
                if c.get("judge", "") == self._active_filter
            ]
        else:
            self._filtered_cells = list(self._all_cells)

        self._rebuild_list()

    def _rebuild_list(self):
        """Rebuild the QListWidget from _filtered_cells using lightweight items."""
        self.list_widget.clear()

        for cell_data in self._filtered_cells:
            item = QListWidgetItem()
            item.setData(ROLE_CELL_ID, cell_data.get("cell_id", ""))
            item.setData(ROLE_JUDGE, cell_data.get("judge", ""))
            item.setData(ROLE_JUDGE_DEFECT, cell_data.get("judge_defect", ""))
            item.setData(ROLE_SIDE, cell_data.get("side", ""))
            item.setSizeHint(QSize(0, 52))
            self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_row_changed(self, row: int):
        """Emit cell_selected when selection changes."""
        if 0 <= row < len(self._filtered_cells):
            self.cell_selected.emit(self._filtered_cells[row])

    def select_next(self):
        current = self.list_widget.currentRow()
        if current < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(current + 1)

    def select_previous(self):
        current = self.list_widget.currentRow()
        if current > 0:
            self.list_widget.setCurrentRow(current - 1)

    def current_index(self) -> int:
        return self.list_widget.currentRow()

    def cell_count(self) -> int:
        return self.list_widget.count()

    def total_cell_count(self) -> int:
        return len(self._all_cells)

    def get_judge_counts(self) -> dict:
        """Count cells by JUDGE type from all (unfiltered) cells."""
        counts = {}
        for cell in self._all_cells:
            judge = cell.get("judge", "")
            counts[judge] = counts.get(judge, 0) + 1
        return counts