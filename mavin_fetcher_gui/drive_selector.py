from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QCheckBox, QGroupBox
)


def allowed_drive_letters() -> list[str]:
    return ["E", "F", "G"]


class DriveSelectorWidget(QWidget):
    """
    Checkbox selector for drives (E/F/G only).
    Provides:
      - to_text(): "E,F"
      - from_text("E,F") -> checks those (ignores others)
      - checked_letters()
    Default: nothing selected.
    """

    def __init__(self):
        super().__init__()

        self._boxes: dict[str, QCheckBox] = {}

        root = QVBoxLayout(self)

        group = QGroupBox("Drives")
        row = QHBoxLayout(group)

        for letter in allowed_drive_letters():
            cb = QCheckBox(letter)
            self._boxes[letter] = cb
            row.addWidget(cb)

        row.addStretch(1)
        root.addWidget(group)

        # ✅ default: none selected
        self.set_all(False)

    def set_all(self, checked: bool) -> None:
        for cb in self._boxes.values():
            cb.setChecked(checked)

    def set_letters(self, letters: list[str]) -> None:
        allowed = set(allowed_drive_letters())
        target = {x.strip().upper().rstrip(":") for x in letters if x.strip()}
        target = {x for x in target if x in allowed}

        for letter, cb in self._boxes.items():
            cb.setChecked(letter in target)

    def checked_letters(self) -> list[str]:
        return [letter for letter, cb in self._boxes.items() if cb.isChecked()]

    def to_text(self) -> str:
        return ",".join(self.checked_letters())

    def from_text(self, drives_text: str) -> None:
        # ✅ empty means "none selected"
        if not drives_text:
            self.set_all(False)
            return
        parts = [x.strip().upper().rstrip(":") for x in drives_text.split(",") if x.strip()]
        self.set_letters(parts)
