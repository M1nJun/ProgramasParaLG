from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QFileDialog, QLineEdit, QTextEdit, QMessageBox, QCheckBox,
    QFrame, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QSizePolicy, QAbstractItemView
)

from core.pcs import load_pcs, PcInfo
from core.fs_ops import get_remote_mavin_root
from core.task_runner import PcTask, TaskRunner


def _hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MAVIN Model Injector (SMB Multi-PC)")
        self.setMinimumSize(1100, 620)

        self.pcs: List[PcInfo] = []
        self.pc_model_maps: Dict[str, Dict[str, Path]] = {}
        self.intersection_models: List[Tuple[str, str]] = []
        self.runner = TaskRunner(max_concurrency=4)

        self._build_ui()
        self._load_pcs()
        self._refresh_models()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        title = QLabel("MAVIN Model Injector (SMB Multi-PC)")
        f = QFont()
        f.setPointSize(18)
        f.setBold(True)
        title.setFont(f)
        root.addWidget(title)

        subtitle = QLabel("Copies over SMB to \\<ip>\C$\VisionPC\Bin\MAVIN\<Model> with overwrite-only + backup into DL_VERSION.")
        subtitle.setStyleSheet("color: #6b7280;")
        root.addWidget(subtitle)
        root.addWidget(_hline())

        top = QHBoxLayout()
        root.addLayout(top, 1)

        # Left: PC selection
        left = QVBoxLayout()
        left.setSpacing(8)
        top.addLayout(left, 0)

        left.addWidget(QLabel("Select PCs:"))
        self.lst_pcs = QListWidget()
        self.lst_pcs.setMinimumWidth(260)
        self.lst_pcs.itemChanged.connect(self._on_pc_selection_changed)
        left.addWidget(self.lst_pcs, 1)

        pc_btns = QHBoxLayout()
        self.btn_all = QPushButton("Select All")
        self.btn_none = QPushButton("Select None")
        self.btn_all.clicked.connect(self._select_all_pcs)
        self.btn_none.clicked.connect(self._select_none_pcs)
        pc_btns.addWidget(self.btn_all)
        pc_btns.addWidget(self.btn_none)
        left.addLayout(pc_btns)

        hint = QLabel("Models dropdown uses INTERSECTION of selected PCs.")
        hint.setStyleSheet("color: #6b7280;")
        left.addWidget(hint)

        # Middle: controls + logs
        mid = QVBoxLayout()
        mid.setSpacing(10)
        top.addLayout(mid, 1)

        src_row = QHBoxLayout()
        src_row.addWidget(QLabel("Source folder to inject:"))
        self.txt_source = QLineEdit()
        self.txt_source.setPlaceholderText("Choose a folder that contains the new model contents...")
        src_row.addWidget(self.txt_source, 1)
        btn_src = QPushButton("Browse")
        btn_src.clicked.connect(self._browse_source)
        src_row.addWidget(btn_src)
        mid.addLayout(src_row)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Target model (intersection):"))
        self.cmb_models = QComboBox()
        self.cmb_models.setMinimumWidth(360)
        model_row.addWidget(self.cmb_models, 1)
        self.btn_refresh_models = QPushButton("Refresh Models")
        self.btn_refresh_models.clicked.connect(self._refresh_models)
        model_row.addWidget(self.btn_refresh_models)
        mid.addLayout(model_row)

        opt_row = QHBoxLayout()
        self.chk_backup = QCheckBox("Save backup into DL_VERSION/<source_folder_name>")
        self.chk_backup.setChecked(True)
        opt_row.addWidget(self.chk_backup)
        opt_row.addStretch(1)

        self.btn_dry_run = QPushButton("Dry Run (marker)")
        self.btn_dry_run.clicked.connect(self._on_dry_run)
        opt_row.addWidget(self.btn_dry_run)

        self.btn_inject = QPushButton("Inject")
        self.btn_inject.clicked.connect(self._on_inject)
        self.btn_inject.setFixedHeight(34)
        self.btn_inject.setStyleSheet("QPushButton { font-weight: 600; }")
        opt_row.addWidget(self.btn_inject)
        mid.addLayout(opt_row)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Logs will appear here...")
        self.log.setStyleSheet("font-family: Consolas, Menlo, monospace; font-size: 12px;")
        mid.addWidget(self.log, 1)

        # Right: per-PC status table
        right = QVBoxLayout()
        right.setSpacing(8)
        top.addLayout(right, 1)

        right.addWidget(QLabel("Per-PC status:"))
        self.tbl = QTableWidget(0, 5)
        self.tbl.setHorizontalHeaderLabels(["PC", "IP", "Status", "Detail", "Progress"])
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tbl.horizontalHeader().setStretchLastSection(True)
        right.addWidget(self.tbl, 1)

        root.addWidget(_hline())
        self.lbl_footer = QLabel("Ready.")
        self.lbl_footer.setStyleSheet("color: #6b7280;")
        root.addWidget(self.lbl_footer)

    # ---------- PC loading / selection ----------
    def _load_pcs(self) -> None:
        try:
            cfg = Path(__file__).resolve().parents[1] / "pcs.json"
            self.pcs = load_pcs(cfg)
        except Exception as e:
            QMessageBox.critical(self, "PC config error", f"Failed to load pcs.json: {e}")
            self.pcs = []

        self.lst_pcs.blockSignals(True)
        self.lst_pcs.clear()
        for pc in self.pcs:
            item = QListWidgetItem(pc.key)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, pc)
            self.lst_pcs.addItem(item)
        self.lst_pcs.blockSignals(False)

        self._append_log(f"Loaded {len(self.pcs)} PCs from pcs.json.")

    def _selected_pcs(self) -> List[PcInfo]:
        out: List[PcInfo] = []
        for i in range(self.lst_pcs.count()):
            it = self.lst_pcs.item(i)
            if it.checkState() == Qt.Checked:
                out.append(it.data(Qt.UserRole))
        return out

    def _select_all_pcs(self) -> None:
        self.lst_pcs.blockSignals(True)
        for i in range(self.lst_pcs.count()):
            self.lst_pcs.item(i).setCheckState(Qt.Checked)
        self.lst_pcs.blockSignals(False)
        self._on_pc_selection_changed()

    def _select_none_pcs(self) -> None:
        self.lst_pcs.blockSignals(True)
        for i in range(self.lst_pcs.count()):
            self.lst_pcs.item(i).setCheckState(Qt.Unchecked)
        self.lst_pcs.blockSignals(False)
        self._on_pc_selection_changed()

    def _on_pc_selection_changed(self) -> None:
        self._refresh_models()

    # ---------- Models (intersection) ----------
    def _refresh_models(self) -> None:
        sel = self._selected_pcs()
        self.cmb_models.clear()
        self.intersection_models = []
        self.pc_model_maps = {}

        if not sel:
            self.cmb_models.addItem("(Select PCs to load models)")
            self.cmb_models.setEnabled(False)
            self._append_log("No PCs selected; models not loaded.")
            self._rebuild_status_table()
            return

        self.cmb_models.setEnabled(True)
        self._append_log("Refreshing models (intersection across selected PCs)...")

        sets: List[Set[str]] = []
        for pc in sel:
            try:
                model_map = self.runner.scan_models_for_pc(pc.ip)
                self.pc_model_maps[pc.key] = model_map
                sets.append(set(model_map.keys()))
                self._append_log(f"{pc.key}: found {len(model_map)} model folders under {get_remote_mavin_root(pc.ip)}")
            except Exception as e:
                self.pc_model_maps[pc.key] = {}
                sets.append(set())
                self._append_log(f"{pc.key}: ERROR scanning models: {e}")

        inter: Set[str] = sets[0].copy()
        for s in sets[1:]:
            inter &= s

        if not inter:
            self.cmb_models.addItem("(No common model folders across selected PCs)")
            self._append_log("Intersection is empty.")
        else:
            ref_pc = sel[0].key
            ref_map = self.pc_model_maps.get(ref_pc, {})
            items: List[Tuple[str, str]] = []
            for canon in sorted(inter):
                actual = ref_map.get(canon)
                display = actual.name if actual else canon
                items.append((canon, display))

            self.intersection_models = items
            for canon, display in items:
                self.cmb_models.addItem(display, userData=canon)

            self._append_log(f"Intersection models: {len(items)}")

        self._rebuild_status_table()

    # ---------- UI helpers ----------
    def _append_log(self, msg: str) -> None:
        self.log.append(msg)

    def _browse_source(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select source folder")
        if folder:
            self.txt_source.setText(folder)

    def _current_model_canonical(self) -> Optional[str]:
        if not self.cmb_models.isEnabled():
            return None
        idx = self.cmb_models.currentIndex()
        canon = self.cmb_models.itemData(idx)
        return str(canon) if canon else None

    def _set_busy(self, busy: bool) -> None:
        self.btn_refresh_models.setEnabled(not busy)
        self.btn_inject.setEnabled(not busy)
        self.btn_dry_run.setEnabled(not busy)
        self.btn_all.setEnabled(not busy)
        self.btn_none.setEnabled(not busy)
        self.lst_pcs.setEnabled(not busy)

    # ---------- Status table ----------
    def _rebuild_status_table(self) -> None:
        sel = self._selected_pcs()
        self.tbl.setRowCount(0)
        for pc in sel:
            row = self.tbl.rowCount()
            self.tbl.insertRow(row)
            self.tbl.setItem(row, 0, QTableWidgetItem(pc.key))
            self.tbl.setItem(row, 1, QTableWidgetItem(pc.ip))
            self.tbl.setItem(row, 2, QTableWidgetItem("READY"))
            self.tbl.setItem(row, 3, QTableWidgetItem(""))
            self.tbl.setItem(row, 4, QTableWidgetItem(""))

    def _row_for_pc(self, pc_key: str) -> int:
        for r in range(self.tbl.rowCount()):
            if self.tbl.item(r, 0).text() == pc_key:
                return r
        return -1

    def _set_row(self, pc_key: str, status: str = None, detail: str = None, progress: str = None) -> None:
        r = self._row_for_pc(pc_key)
        if r < 0:
            return
        if status is not None:
            self.tbl.item(r, 2).setText(status)
        if detail is not None:
            self.tbl.item(r, 3).setText(detail)
        if progress is not None:
            self.tbl.item(r, 4).setText(progress)

    # ---------- Run ----------
    def _validate_before_run(self):
        sel = self._selected_pcs()
        if not sel:
            QMessageBox.warning(self, "No PCs selected", "Select at least one PC.")
            return None, None, []
        src = Path(self.txt_source.text().strip())
        if not src.exists() or not src.is_dir():
            QMessageBox.warning(self, "Missing source", "Please choose a valid source folder.")
            return None, None, []
        canon = self._current_model_canonical()
        if not canon or canon.startswith("("):
            QMessageBox.warning(self, "Missing model", "Please select a model from the dropdown.")
            return None, None, []
        return src, canon, sel

    def _connect_runnable(self, r):
        r.signals.log.connect(self._on_task_log)
        r.signals.status.connect(self._on_task_status)
        r.signals.progress.connect(self._on_task_progress)
        r.signals.finished.connect(self._on_task_finished)

    def _start_tasks(self, *, dry_run: bool) -> None:
        src, canon, sel = self._validate_before_run()
        if not sel:
            return

        mode = "DRY RUN (marker files only)" if dry_run else "INJECTION (copy files)"
        msg = (
            f"Mode: {mode}\n\n"
            f"Selected PCs: {len(sel)}\n"
            f"Model (canonical): {canon}\n"
            f"Source: {src}\n\n"
            "Continue?"
        )
        if QMessageBox.question(self, "Confirm", msg, QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        self._append_log("----")
        self._append_log(f"Starting {mode} ...")
        self._set_busy(True)
        self.lbl_footer.setText(f"Running {mode} ...")
        self._rebuild_status_table()

        for pc in sel:
            model_map = self.pc_model_maps.get(pc.key, {})
            task = PcTask(
                pc_key=pc.key,
                ip=pc.ip,
                model_canonical=canon,
                source_folder=src,
                do_backup=self.chk_backup.isChecked(),
                dry_run=dry_run,
            )

            def connect(rr):
                self._connect_runnable(rr)

            self.runner.start_task(task, model_map, connect=connect)

    def _on_dry_run(self) -> None:
        self._start_tasks(dry_run=True)

    def _on_inject(self) -> None:
        self._start_tasks(dry_run=False)

    # ---------- Signal handlers ----------
    def _on_task_log(self, pc_key: str, message: str) -> None:
        self._append_log(f"[{pc_key}] {message}")

    def _on_task_status(self, pc_key: str, status: str, detail: str) -> None:
        self._set_row(pc_key, status=status, detail=detail)

    def _on_task_progress(self, pc_key: str, cur: int, total: int) -> None:
        self._set_row(pc_key, progress=f"{cur}/{total}" if total > 0 else "")

    def _on_task_finished(self, pc_key: str, success: bool, message: str) -> None:
        self._set_row(pc_key, detail=message)
        # Re-enable if no rows are READY/RUNNING/DRY RUN
        done = True
        for r in range(self.tbl.rowCount()):
            st = self.tbl.item(r, 2).text().upper()
            if st in ("READY", "RUNNING", "DRY RUN"):
                done = False
                break
        if done:
            self._set_busy(False)
            self.lbl_footer.setText("Ready.")
