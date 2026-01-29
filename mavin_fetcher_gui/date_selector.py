from __future__ import annotations

from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QDateEdit,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox
)


class DateSelectorWidget(QWidget):
    """
    Date selection widget supporting:
      - Single date
      - Date range
      - Specific dates (list)

    Provides:
      - export_state() -> dict
      - import_state(dict)
      - current_mode_text()
      - current_date_text()  (string representation used by older worker)

    NEW for SessionPanel:
      - changed signal emitted when user changes anything
    """

    changed = pyqtSignal()

    MODES = ["Single date", "Date range", "Specific dates"]

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Mode selector
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Date mode:"))
        self.mode = QComboBox()
        self.mode.addItems(self.MODES)
        mode_row.addWidget(self.mode)
        mode_row.addStretch(1)
        root.addLayout(mode_row)

        # Single date
        self.single_row = QHBoxLayout()
        self.single_row.addWidget(QLabel("Date:"))
        self.single_date = QDateEdit()
        self.single_date.setCalendarPopup(True)
        self.single_date.setDisplayFormat("yyyy-MM-dd")
        self.single_date.setDate(QDate.currentDate())
        self.single_row.addWidget(self.single_date)
        self.single_row.addStretch(1)
        root.addLayout(self.single_row)

        # Range
        self.range_row = QHBoxLayout()
        self.range_row.addWidget(QLabel("Start:"))
        self.range_start = QDateEdit()
        self.range_start.setCalendarPopup(True)
        self.range_start.setDisplayFormat("yyyy-MM-dd")
        self.range_start.setDate(QDate.currentDate())

        self.range_row.addWidget(self.range_start)
        self.range_row.addSpacing(12)

        self.range_row.addWidget(QLabel("End:"))
        self.range_end = QDateEdit()
        self.range_end.setCalendarPopup(True)
        self.range_end.setDisplayFormat("yyyy-MM-dd")
        self.range_end.setDate(QDate.currentDate())

        self.range_row.addWidget(self.range_end)
        self.range_row.addStretch(1)
        root.addLayout(self.range_row)

        # Specific dates list
        self.list_row = QVBoxLayout()
        list_top = QHBoxLayout()
        list_top.addWidget(QLabel("Specific dates:"))
        list_top.addStretch(1)
        self.list_row.addLayout(list_top)

        list_controls = QHBoxLayout()
        self.add_btn = QPushButton("Add")
        self.remove_btn = QPushButton("Remove selected")
        self.clear_btn = QPushButton("Clear")
        list_controls.addWidget(self.add_btn)
        list_controls.addWidget(self.remove_btn)
        list_controls.addWidget(self.clear_btn)
        list_controls.addStretch(1)
        self.list_row.addLayout(list_controls)

        self.specific_date_picker = QDateEdit()
        self.specific_date_picker.setCalendarPopup(True)
        self.specific_date_picker.setDisplayFormat("yyyy-MM-dd")
        self.specific_date_picker.setDate(QDate.currentDate())
        self.list_row.addWidget(self.specific_date_picker)

        self.list_widget = QListWidget()
        self.list_row.addWidget(self.list_widget)

        root.addLayout(self.list_row)

        # Wiring
        self.mode.currentIndexChanged.connect(self._update_visible_rows)
        self.mode.currentIndexChanged.connect(lambda: self.changed.emit())

        self.single_date.dateChanged.connect(lambda: self.changed.emit())
        self.range_start.dateChanged.connect(lambda: self.changed.emit())
        self.range_end.dateChanged.connect(lambda: self.changed.emit())
        self.specific_date_picker.dateChanged.connect(lambda: self.changed.emit())

        self.add_btn.clicked.connect(self._on_add)
        self.remove_btn.clicked.connect(self._on_remove)
        self.clear_btn.clicked.connect(self._on_clear)

        self.list_widget.itemSelectionChanged.connect(lambda: self.changed.emit())

        # Initialize visibility
        self._update_visible_rows()

    def _update_visible_rows(self) -> None:
        mode = self.current_mode_text()

        single = (mode == "Single date")
        rng = (mode == "Date range")
        spec = (mode == "Specific dates")

        # show/hide rows
        self._set_layout_visible(self.single_row, single)
        self._set_layout_visible(self.range_row, rng)
        self._set_layout_visible(self.list_row, spec)

    def _set_layout_visible(self, layout, visible: bool) -> None:
        # Works for QHBoxLayout/QVBoxLayout by toggling contained widgets
        for i in range(layout.count()):
            item = layout.itemAt(i)
            w = item.widget()
            if w is not None:
                w.setVisible(visible)
            else:
                child_layout = item.layout()
                if child_layout is not None:
                    self._set_layout_visible(child_layout, visible)

    def current_mode_text(self) -> str:
        return self.mode.currentText()

    def _on_add(self) -> None:
        d = self.specific_date_picker.date().toString("yyyy-MM-dd")
        existing = set(self._list_values())
        if d in existing:
            QMessageBox.information(self, "Already added", f"{d} is already in the list.")
            return
        self.list_widget.addItem(QListWidgetItem(d))
        self._sort_list()
        self.changed.emit()

    def _on_remove(self) -> None:
        for it in self.list_widget.selectedItems():
            row = self.list_widget.row(it)
            self.list_widget.takeItem(row)
        self.changed.emit()

    def _on_clear(self) -> None:
        self.list_widget.clear()
        self.changed.emit()

    def _list_values(self) -> list[str]:
        return [self.list_widget.item(i).text().strip() for i in range(self.list_widget.count())]

    def _sort_list(self) -> None:
        vals = sorted(set(self._list_values()))
        self.list_widget.clear()
        for v in vals:
            self.list_widget.addItem(QListWidgetItem(v))

    def export_state(self) -> dict:
        mode = self.current_mode_text()

        state = {
            "date_mode": mode,
            "single_date": self.single_date.date().toString("yyyy-MM-dd"),
            "range_start": self.range_start.date().toString("yyyy-MM-dd"),
            "range_end": self.range_end.date().toString("yyyy-MM-dd"),
            "specific_dates": self._list_values(),
        }
        return state

    def import_state(self, state: dict) -> None:
        if not state:
            return

        mode = state.get("date_mode", "Single date")
        if mode not in self.MODES:
            mode = "Single date"

        # Prevent noisy changed signals while importing
        self.blockSignals(True)
        try:
            self.mode.setCurrentText(mode)

            sd = state.get("single_date", "") or ""
            rs = state.get("range_start", "") or ""
            re = state.get("range_end", "") or ""

            if sd:
                self.single_date.setDate(QDate.fromString(sd, "yyyy-MM-dd"))
            if rs:
                self.range_start.setDate(QDate.fromString(rs, "yyyy-MM-dd"))
            if re:
                self.range_end.setDate(QDate.fromString(re, "yyyy-MM-dd"))

            dates = state.get("specific_dates", []) or []
            self.list_widget.clear()
            for d in sorted(set(dates)):
                self.list_widget.addItem(QListWidgetItem(d))

            self._update_visible_rows()
        finally:
            self.blockSignals(False)

        # One clean notification
        self.changed.emit()

    def current_date_text(self) -> str:
        """
        Older helper used by earlier worker versions.
        Returns:
          - single date: "YYYY-MM-DD"
          - range: "YYYY-MM-DD YYYY-MM-DD"
          - specific: "YYYY-MM-DD,YYYY-MM-DD,..."
        """
        mode = self.current_mode_text()
        if mode == "Single date":
            return self.single_date.date().toString("yyyy-MM-dd")
        if mode == "Date range":
            return f"{self.range_start.date().toString('yyyy-MM-dd')} {self.range_end.date().toString('yyyy-MM-dd')}"
        # specific
        return ",".join(self._list_values())
