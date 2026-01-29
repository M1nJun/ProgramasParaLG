from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLabel


class StatusBarLabel(QLabel):
    """
    Simple status banner for tabs.
    - Call set_success / set_info / set_error
    - Auto-clears after N ms (default 2000)
    """
    def __init__(self, *, clear_ms: int = 2000):
        super().__init__("")
        self._clear_ms = int(clear_ms)
        self.setWordWrap(True)
        self.setMinimumHeight(18)
        self.setStyleSheet("padding: 6px; border-radius: 6px;")

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.clear_status)

        self.clear_status()

    def clear_status(self) -> None:
        self._timer.stop()
        self.setText("")
        # hidden when empty so layout stays clean
        self.setVisible(False)

    def _show(self, text: str, css: str) -> None:
        self._timer.stop()
        self.setVisible(True)
        self.setText(text)
        self.setStyleSheet(css)
        self._timer.start(self._clear_ms)

    def set_success(self, text: str) -> None:
        self._show(text, "padding: 6px; border-radius: 6px; background: #E8F5E9;")

    def set_info(self, text: str) -> None:
        self._show(text, "padding: 6px; border-radius: 6px; background: #E3F2FD;")

    def set_error(self, text: str) -> None:
        self._show(text, "padding: 6px; border-radius: 6px; background: #FFEBEE;")
