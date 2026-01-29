from __future__ import annotations

from PyQt6.QtWidgets import QFileDialog, QWidget


def pick_folder(parent: QWidget, title: str, start_dir: str = "") -> str:
    return QFileDialog.getExistingDirectory(parent, title, start_dir)


def pick_files(parent: QWidget, title: str, start_dir: str = "", filter_str: str = "CSV Files (*.csv);;Excel Files (*.xlsx *.xlsm);;All Files (*.*)") -> list[str]:
    paths, _ = QFileDialog.getOpenFileNames(parent, title, start_dir, filter_str)
    return paths
