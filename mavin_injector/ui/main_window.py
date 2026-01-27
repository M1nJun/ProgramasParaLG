from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QFileDialog, QLineEdit, QTextEdit, QProgressBar, QMessageBox, QCheckBox, QFrame
)

from core.fs_ops import locate_mavin_root, list_model_folders
from core.worker import InjectJob, InjectWorker


def _hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MAVIN Model Injector")
        self.setMinimumSize(820, 520)

        self.mavin_root = None
        self.model_folders: List[Path] = []
        self.worker: Optional[InjectWorker] = None

        self._build_ui()
        self._load_mavin()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        title = QLabel("MAVIN Model Injector")
        f = QFont()
        f.setPointSize(18)
        f.setBold(True)
        title.setFont(f)
        root.addWidget(title)

        subtitle = QLabel("Overwrite-only copy into a model folder + backup in DL_VERSION.")
        subtitle.setStyleSheet("color: #6b7280;")
        root.addWidget(subtitle)

        root.addWidget(_hline())

        self.lbl_mavin = QLabel("MAVIN root: (detecting...)")
        self.lbl_mavin.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(self.lbl_mavin)

        src_row = QHBoxLayout()
        src_row.addWidget(QLabel("Source folder to inject:"))
        self.txt_source = QLineEdit()
        self.txt_source.setPlaceholderText("Choose a folder that contains the new model contents...")
        src_row.addWidget(self.txt_source, 1)
        btn_src = QPushButton("Browse")
        btn_src.clicked.connect(self._browse_source)
        src_row.addWidget(btn_src)
        root.addLayout(src_row)

        tgt_row = QHBoxLayout()
        tgt_row.addWidget(QLabel("Target model folder:"))
        self.cmb_models = QComboBox()
        self.cmb_models.setMinimumWidth(320)
        tgt_row.addWidget(self.cmb_models)
        self.txt_custom_target = QLineEdit()
        self.txt_custom_target.setPlaceholderText("Optional custom path (overrides dropdown)...")
        tgt_row.addWidget(self.txt_custom_target, 1)
        btn_tgt = QPushButton("Browse")
        btn_tgt.clicked.connect(self._browse_target)
        tgt_row.addWidget(btn_tgt)
        root.addLayout(tgt_row)

        opt_row = QHBoxLayout()
        self.chk_backup = QCheckBox("Save backup into DL_VERSION/<source_folder_name>")
        self.chk_backup.setChecked(True)
        opt_row.addWidget(self.chk_backup)
        opt_row.addStretch(1)
        root.addLayout(opt_row)

        btn_row = QHBoxLayout()
        self.btn_refresh = QPushButton("Refresh Models")
        self.btn_refresh.clicked.connect(self._load_mavin)
        btn_row.addWidget(self.btn_refresh)

        btn_row.addStretch(1)

        self.btn_inject = QPushButton("Inject")
        self.btn_inject.clicked.connect(self._on_inject)
        self.btn_inject.setFixedHeight(36)
        self.btn_inject.setStyleSheet("QPushButton { font-weight: 600; }")
        btn_row.addWidget(self.btn_inject)
        root.addLayout(btn_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Logs will appear here...")
        self.log.setStyleSheet("font-family: Consolas, Menlo, monospace; font-size: 12px;")
        root.addWidget(self.log, 1)

    def _append_log(self, msg: str) -> None:
        self.log.append(msg)

    def _load_mavin(self) -> None:
        self.cmb_models.clear()
        self.model_folders = []
        self.mavin_root = locate_mavin_root()

        if not self.mavin_root:
            self.lbl_mavin.setText("MAVIN root: NOT FOUND. Expected under C:\\VisionPC\\Bin\\(MAVIN|mavin)")
            self._append_log("ERROR: Could not locate MAVIN root folder.")
            self.cmb_models.setEnabled(False)
            return

        self.lbl_mavin.setText(f"MAVIN root: {self.mavin_root.path}  (auto-detected)")
        self.model_folders = list_model_folders(self.mavin_root.path)

        if not self.model_folders:
            self.cmb_models.addItem("(No folders found)")
            self.cmb_models.setEnabled(False)
        else:
            self.cmb_models.setEnabled(True)
            for p in self.model_folders:
                self.cmb_models.addItem(p.name, userData=str(p))

        self._append_log("Loaded model folders.")

    def _browse_source(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select source folder")
        if folder:
            self.txt_source.setText(folder)

    def _browse_target(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select target model folder")
        if folder:
            self.txt_custom_target.setText(folder)

    def _resolve_target_folder(self) -> Optional[Path]:
        custom = self.txt_custom_target.text().strip()
        if custom:
            return Path(custom)

        if not self.model_folders or not self.cmb_models.isEnabled():
            return None

        idx = self.cmb_models.currentIndex()
        data = self.cmb_models.itemData(idx)
        if data:
            return Path(str(data))

        name = self.cmb_models.currentText()
        if self.mavin_root:
            return self.mavin_root.path / name
        return None

    def _set_busy(self, busy: bool) -> None:
        self.btn_inject.setEnabled(not busy)
        self.btn_refresh.setEnabled(not busy)

    def _on_inject(self) -> None:
        src = Path(self.txt_source.text().strip())
        tgt = self._resolve_target_folder()

        if not src.exists() or not src.is_dir():
            QMessageBox.warning(self, "Missing source", "Please choose a valid source folder.")
            return
        if not tgt or not tgt.exists() or not tgt.is_dir():
            QMessageBox.warning(self, "Missing target", "Please choose a valid target model folder.")
            return

        msg = (
            f"This will OVERWRITE files in:\n\n{tgt}\n\n"
            f"Using source:\n\n{src}\n\n"
            "Old files/folders that are not in the source will be left as-is.\n\n"
            "Continue?"
        )
        if QMessageBox.question(self, "Confirm Injection", msg, QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        self._append_log("----")
        self._append_log("Starting injection...")

        self._set_busy(True)
        self.progress.setValue(0)

        job = InjectJob(source_folder=src, target_model_folder=tgt, do_backup=self.chk_backup.isChecked())
        self.worker = InjectWorker(job)
        self.worker.signals.log.connect(self._append_log)
        self.worker.signals.progress.connect(self._on_progress)
        self.worker.signals.done.connect(self._on_done)
        self.worker.start()

    def _on_progress(self, cur: int, total: int) -> None:
        if total <= 0:
            self.progress.setRange(0, 0)
            return
        self.progress.setRange(0, total)
        self.progress.setValue(cur)

    def _on_done(self, success: bool, message: str) -> None:
        self._append_log(message)
        self._set_busy(False)
        if success:
            QMessageBox.information(self, "Done", message)
        else:
            QMessageBox.critical(self, "Error", message)
