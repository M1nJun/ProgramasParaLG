from __future__ import annotations

from PyQt6.QtWidgets import QTextEdit


class LogWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)

    def append_line(self, text: str) -> None:
        self.append(text)
        self.ensureCursorVisible()
