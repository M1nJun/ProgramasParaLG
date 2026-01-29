from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QCheckBox, QGroupBox, QLabel
)


def allowed_drive_letters() -> list[str]:
    return ["E", "F", "G"]


class DriveSelectorWidget(QWidget):
    """
    Checkbox selector for drives (E/F/G only) with presets.
    Provides:
      - to_text(): "E,F,G"
      - from_text("E,F") -> checks those (ignores others)
      - checked_letters()
    """

    def __init__(self):
        super().__init__()

        self._boxes: dict[str, QCheckBox] = {}

        root = QVBoxLayout(self)

        presets = QHBoxLayout()
        presets.addWidget(QLabel("Presets:"))

        self.btn_all = QPushButton("E,F,G")
        self.btn_ef = QPushButton("E,F")
        self.btn_f = QPushButton("F only")
        self.btn_clear = QPushButton("Clear")

        presets.addWidget(self.btn_all)
        presets.addWidget(self.btn_ef)
        presets.addWidget(self.btn_f)
        presets.addWidget(self.btn_clear)
        presets.addStretch(1)
        root.addLayout(presets)

        group = QGroupBox("Drives")
        row = QHBoxLayout(group)

        for letter in allowed_drive_letters():
            cb = QCheckBox(letter)
            self._boxes[letter] = cb
            row.addWidget(cb)

        row.addStretch(1)
        root.addWidget(group)

        # default: all checked
        self.set_letters(allowed_drive_letters())

        self.btn_all.clicked.connect(lambda: self.set_letters(allowed_drive_letters()))
        self.btn_ef.clicked.connect(lambda: self.set_letters(["E", "F"]))
        self.btn_f.clicked.connect(lambda: self.set_letters(["F"]))
        self.btn_clear.clicked.connect(lambda: self.set_all(False))

    def set_all(self, checked: bool) -> None:
        for cb in self._boxes.values():
            cb.setChecked(checked)

    def set_letters(self, letters: list[str]) -> None:
        allowed = set(allowed_drive_letters())
        target = {x.strip().upper().rstrip(":") for x in letters if x.strip()}
        # ignore anything not in allowed
        target = {x for x in target if x in allowed}

        for letter, cb in self._boxes.items():
            cb.setChecked(letter in target)

    def checked_letters(self) -> list[str]:
        return [letter for letter, cb in self._boxes.items() if cb.isChecked()]

    def to_text(self) -> str:
        return ",".join(self.checked_letters())

    def from_text(self, drives_text: str) -> None:
        if not drives_text:
            self.set_letters(allowed_drive_letters())
            return
        parts = [x.strip().upper().rstrip(":") for x in drives_text.split(",") if x.strip()]
        self.set_letters(parts)
