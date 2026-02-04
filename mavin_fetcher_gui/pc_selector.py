from __future__ import annotations

from typing import Dict, List

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QPushButton, QCheckBox, QLabel,
    QGridLayout
)

from mavin_fetcher.pc_registry import load_registry, sorted_keys, PcRegistryError


class PcSelectorWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, columns: int = 4):
        """
        columns: how many checkbox columns to show (4 works well for ~16 PCs).
        """
        super().__init__()
        self._boxes: Dict[str, QCheckBox] = {}
        self._columns = max(1, int(columns))

        root = QVBoxLayout(self)

        group = QGroupBox("PCs (Remote)")
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(6)

        # Buttons row
        btn_row = QHBoxLayout()
        self.btn_all = QPushButton("Select All")
        self.btn_none = QPushButton("None")
        btn_row.addWidget(self.btn_all)
        btn_row.addWidget(self.btn_none)
        btn_row.addStretch(1)
        group_layout.addLayout(btn_row)

        # Status line (small)
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("font-size: 11px;")
        group_layout.addWidget(self._status_label)

        # Grid for PCs (no scrolling)
        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(2, 2, 2, 2)
        self._grid.setHorizontalSpacing(14)
        self._grid.setVerticalSpacing(6)
        group_layout.addWidget(self._grid_host)

        root.addWidget(group)

        self.btn_all.clicked.connect(self.select_all)
        self.btn_none.clicked.connect(self.select_none)

        self._load_from_registry()

    def _clear_grid(self) -> None:
        # Remove all widgets from grid layout
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _load_from_registry(self) -> None:
        try:
            reg = load_registry()
            keys = sorted_keys(reg)
        except PcRegistryError as e:
            self._status_label.setText(f"[pcs.json error] {e}")
            self._clear_grid()
            self._boxes.clear()
            return

        self._status_label.setText(f"Loaded {len(keys)} PCs")

        # rebuild
        self._clear_grid()
        self._boxes.clear()

        for i, k in enumerate(keys):
            r = i // self._columns
            c = i % self._columns
            cb = QCheckBox(k)
            cb.setChecked(False)  # default none selected
            cb.stateChanged.connect(lambda *_: self.changed.emit())
            self._boxes[k] = cb
            self._grid.addWidget(cb, r, c)

        # stretch last column a bit so grid doesn't look cramped
        self._grid.setColumnStretch(self._columns, 1)

        self.changed.emit()

    def select_all(self) -> None:
        for cb in self._boxes.values():
            cb.setChecked(True)
        self.changed.emit()

    def select_none(self) -> None:
        for cb in self._boxes.values():
            cb.setChecked(False)
        self.changed.emit()

    def selected_keys(self) -> List[str]:
        return [k for k, cb in self._boxes.items() if cb.isChecked()]

    def set_selected_keys(self, keys: List[str]) -> None:
        wanted = set(keys or [])
        for k, cb in self._boxes.items():
            cb.setChecked(k in wanted)
        self.changed.emit()

    def set_columns(self, columns: int) -> None:
        """
        Optional helper if you ever want to change layout dynamically.
        """
        self._columns = max(1, int(columns))
        # Re-layout current boxes
        keys = list(self._boxes.keys())
        self._clear_grid()
        for i, k in enumerate(keys):
            r = i // self._columns
            c = i % self._columns
            self._grid.addWidget(self._boxes[k], r, c)
        self._grid.setColumnStretch(self._columns, 1)
