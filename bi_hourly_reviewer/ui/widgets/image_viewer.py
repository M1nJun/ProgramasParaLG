"""
Image Viewer Widget.

Responsibilities:
    - Display images from a cell's output directory.
    - Navigate between images with left/right arrow keys.
    - Show image filename and position indicator.
    - Scale images to fit the available space.
"""

import os
from typing import List

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QFont, QKeyEvent

from ui.styles import COLORS, FONT_FAMILY_MONO, SPACING_SM, SPACING_MD, SPACING_LG


class ImageViewer(QWidget):
    """
    Displays images from a directory with arrow key navigation.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image_paths: List[str] = []
        self._current_index: int = -1
        self._cell_id: str = ""
        self._judge_defect: str = ""
        self._side: str = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar with cell info
        self.header = QWidget()
        self.header.setFixedHeight(36)
        self.header.setStyleSheet(
            f"background-color: {COLORS['bg_header']};"
        )
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(SPACING_LG, 0, SPACING_LG, 0)

        self.cell_info_label = QLabel("No cell selected")
        self.cell_info_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; "
            f"font-weight: 600; font-size: 10pt;"
        )
        header_layout.addWidget(self.cell_info_label)

        header_layout.addStretch()

        self.image_counter_label = QLabel("")
        self.image_counter_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 9pt;"
        )
        header_layout.addWidget(self.image_counter_label)

        layout.addWidget(self.header)

        # Image display area
        self.image_container = QWidget()
        self.image_container.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']};"
        )
        container_layout = QVBoxLayout(self.image_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']};"
        )
        container_layout.addWidget(self.image_label)

        layout.addWidget(self.image_container)

        # Footer bar with filename
        self.footer = QWidget()
        self.footer.setFixedHeight(32)
        self.footer.setStyleSheet(
            f"background-color: {COLORS['bg_header']};"
        )
        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(SPACING_LG, 0, SPACING_LG, 0)

        self.filename_label = QLabel("")
        self.filename_label.setFont(QFont(FONT_FAMILY_MONO, 8))
        self.filename_label.setStyleSheet(
            f"color: {COLORS['text_muted']};"
        )
        footer_layout.addWidget(self.filename_label)

        footer_layout.addStretch()

        self.nav_hint_label = QLabel("← → Navigate images    ↑ ↓ Navigate cells")
        self.nav_hint_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 8pt;"
        )
        footer_layout.addWidget(self.nav_hint_label)

        layout.addWidget(self.footer)

        # Show placeholder
        self._show_placeholder()

    def set_cell_info(self, cell_id: str, judge_defect: str, side: str):
        """Update the cell info display in the header."""
        self._cell_id = cell_id
        self._judge_defect = judge_defect
        self._side = side

        side_text = {"UPPER": "▲ Upper", "LOWER": "▼ Lower", "BOTH": "◆ Both"}.get(
            side, side
        )
        self.cell_info_label.setText(
            f"{cell_id}    |    {judge_defect}    |    {side_text}"
        )

    def load_images_from_directory(self, directory: str):
        """
        Load all image files from a directory.

        Args:
            directory: Path to the cell's output image directory.
        """
        self._image_paths = []
        self._current_index = -1

        if not os.path.isdir(directory):
            self._show_placeholder("Directory not found")
            return

        extensions = {".jpg", ".jpeg", ".png", ".bmp"}
        files = sorted(
            f for f in os.listdir(directory)
            if os.path.splitext(f)[1].lower() in extensions
        )

        self._image_paths = [os.path.join(directory, f) for f in files]

        if self._image_paths:
            self._current_index = 0
            self._display_current()
        else:
            self._show_placeholder("No images found")

    def load_images_from_paths(self, paths: List[str]):
        """
        Load images from an explicit list of file paths.

        Args:
            paths: List of image file paths.
        """
        self._image_paths = [p for p in paths if os.path.isfile(p)]
        self._current_index = 0 if self._image_paths else -1

        if self._image_paths:
            self._display_current()
        else:
            self._show_placeholder("No images found")

    def clear(self):
        """Clear the viewer."""
        self._image_paths = []
        self._current_index = -1
        self._cell_id = ""
        self._judge_defect = ""
        self._side = ""
        self.cell_info_label.setText("No cell selected")
        self._show_placeholder()

    def navigate_next(self):
        """Move to the next image."""
        if self._current_index < len(self._image_paths) - 1:
            self._current_index += 1
            self._display_current()

    def navigate_previous(self):
        """Move to the previous image."""
        if self._current_index > 0:
            self._current_index -= 1
            self._display_current()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle left/right arrow keys for image navigation."""
        if event.key() == Qt.Key_Right:
            self.navigate_next()
        elif event.key() == Qt.Key_Left:
            self.navigate_previous()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        """Re-render current image when widget is resized."""
        super().resizeEvent(event)
        if self._current_index >= 0:
            self._display_current()

    def _display_current(self):
        """Display the image at the current index."""
        if not (0 <= self._current_index < len(self._image_paths)):
            return

        path = self._image_paths[self._current_index]
        pixmap = QPixmap(path)

        if pixmap.isNull():
            self.image_label.setText("Failed to load image")
            self.image_label.setStyleSheet(
                f"color: {COLORS['accent_red']}; "
                f"background-color: {COLORS['bg_secondary']};"
            )
        else:
            # Scale to fit the available space while maintaining aspect ratio
            available = self.image_label.size()
            scaled = pixmap.scaled(
                available,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)

        # Update labels
        self._update_counter()
        self.filename_label.setText(os.path.basename(path))

    def _show_placeholder(self, text: str = "Select a cell to view images"):
        """Show a placeholder message when no image is displayed."""
        self.image_label.clear()
        self.image_label.setText(text)
        self.image_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; "
            f"font-size: 12pt; "
            f"background-color: {COLORS['bg_secondary']};"
        )
        self.image_counter_label.setText("")
        self.filename_label.setText("")

    def _update_counter(self):
        """Update the image position counter."""
        total = len(self._image_paths)
        if total > 0:
            self.image_counter_label.setText(
                f"Image {self._current_index + 1} / {total}"
            )
        else:
            self.image_counter_label.setText("")