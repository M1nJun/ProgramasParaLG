from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem


class BreakdownTableWidget(QTableWidget):
    """
    Displays group breakdown (By Line / By PC):
      Group | Total Cells | Total Rows | Top Class | Top Class Cells
    """

    def __init__(self):
        super().__init__(0, 5)
        self.setHorizontalHeaderLabels(["Group", "Total Cells", "Total Rows", "Top Class", "Top Class Cells"])
        self.setSortingEnabled(True)
        self.setWordWrap(False)

        hdr = self.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

    def set_groups(self, groups: dict) -> None:
        self.setSortingEnabled(False)
        self.setRowCount(0)

        if not groups:
            self.setSortingEnabled(True)
            return

        items = sorted(groups.items(), key=lambda kv: int(kv[1].get("total_cells", 0)), reverse=True)
        self.setRowCount(len(items))

        for r, (group_key, g) in enumerate(items):
            total_cells = int(g.get("total_cells", 0))
            total_rows = int(g.get("total_rows", 0))

            top_cls = ""
            top_cells = 0
            classes = g.get("classes", {}) or {}
            for cls, payload in classes.items():
                c = int(payload.get("cells", 0))
                if c > top_cells:
                    top_cells = c
                    top_cls = cls

            self._set_text(r, 0, str(group_key))
            self._set_num(r, 1, total_cells)
            self._set_num(r, 2, total_rows)
            self._set_text(r, 3, top_cls)
            self._set_num(r, 4, top_cells)

        self.resizeColumnsToContents()
        self.setSortingEnabled(True)

    def _set_text(self, row: int, col: int, s: str) -> None:
        it = QTableWidgetItem(s)
        it.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.setItem(row, col, it)

    def _set_num(self, row: int, col: int, n: int) -> None:
        it = QTableWidgetItem(str(int(n)))
        it.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        it.setData(Qt.ItemDataRole.UserRole, float(n))
        self.setItem(row, col, it)