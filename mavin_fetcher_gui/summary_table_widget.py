from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem


class SummaryTableWidget(QTableWidget):
    class_selected = pyqtSignal(str)  # emits normalized class key like NG_CRITICAL

    def __init__(self):
        super().__init__()
        self.setSortingEnabled(True)

        self.cellDoubleClicked.connect(self._on_double_click)

    def _on_double_click(self, row: int, col: int) -> None:
        # Class column is 0
        it = self.item(row, 0)
        if not it:
            return
        cls = it.text().strip()
        if cls:
            self.class_selected.emit(cls)

    def set_summary_data(self, data: dict) -> None:
        self.setSortingEnabled(False)
        self.clear()

        if not data or "classes" not in data:
            self.setRowCount(0)
            self.setColumnCount(0)
            self.setSortingEnabled(True)
            return

        regions = data.get("regions", [])
        headers = ["Class", "Cells", "Occurrences"] + regions
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        classes = data["classes"]  # dict
        rows = []
        for cls, payload in classes.items():
            cells = int(payload.get("cells", 0))
            occ = int(payload.get("occurrences", 0))
            by_region = payload.get("by_region", {})
            rows.append((cls, cells, occ, by_region))

        rows.sort(key=lambda x: x[1], reverse=True)

        self.setRowCount(len(rows))

        for r, (cls, cells, occ, by_region) in enumerate(rows):
            self._set_item(r, 0, cls, is_num=False)
            self._set_item(r, 1, cells, is_num=True)
            self._set_item(r, 2, occ, is_num=True)
            for c, region in enumerate(regions, start=3):
                self._set_item(r, c, int(by_region.get(region, 0)), is_num=True)

        self.resizeColumnsToContents()
        self.setSortingEnabled(True)

    def _set_item(self, row: int, col: int, value, *, is_num: bool) -> None:
        it = QTableWidgetItem(str(value))
        if is_num:
            it.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
            it.setData(Qt.ItemDataRole.UserRole, float(value))
        else:
            it.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.setItem(row, col, it)
