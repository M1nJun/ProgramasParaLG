from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QScrollArea, QWidget, QVBoxLayout


class ImagePreview(QWidget):
    def __init__(self):
        super().__init__()
        self._path: Optional[Path] = None
        self._pix: Optional[QPixmap] = None

        root = QVBoxLayout(self)
        self.label = QLabel("No image selected")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.label)

        root.addWidget(self.scroll)

    def set_image(self, path: Optional[Path]) -> None:
        self._path = path
        if not path or not path.exists():
            self._pix = None
            self.label.setText("Image not found")
            return

        pix = QPixmap(str(path))
        if pix.isNull():
            self._pix = None
            self.label.setText("Failed to load image")
            return

        self._pix = pix
        self._render_scaled()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._render_scaled()

    def _render_scaled(self) -> None:
        if not self._pix:
            return
        w = max(10, self.scroll.viewport().width() - 10)
        h = max(10, self.scroll.viewport().height() - 10)
        scaled = self._pix.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.label.setPixmap(scaled)
