from __future__ import annotations

from PyQt6.QtWidgets import QScrollArea, QWidget


def wrap_scroll(widget: QWidget) -> QScrollArea:
    """
    Wrap any QWidget inside a QScrollArea so the content can scroll
    if the window is too small.
    """
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(widget)
    return scroll
