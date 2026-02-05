from __future__ import annotations

from pathlib import Path
import traceback
from typing import Any

from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QComboBox, QSplitter
)

from pc_config import load_pcs_config, PCEntry
from multi_pc_checker import PCCheckResult
from ui_pc_details import PCDetailsDialog
from workers import MultiPCCheckWorker
from multi_exporter_csv import export_all_pcs_summary_csv

from ui_multi_detail_pane import MultiDetailPane


class MultiPCWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.base_dir = Path(__file__).resolve().parent
        self.reports_dir = self.base_dir / "reports"
        self.kickout_root = self.base_dir / "KickoutLists"
        self.pcs_json = self.base_dir / "pcs.json"
        self._ensure_reports_dir()

        self._pcs: list[PCEntry] = []
        self._results: list[Any] = []  # keep tolerant while debugging
        self._worker: MultiPCCheckWorker | None = None

        self._build_ui()
        self._load_pcs()
        self._reset_screen()  # clean start

    def _ensure_reports_dir(self):
        try:
            self.reports_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # If this fails, we still run; logging just won't work.
            pass

    def _log_crash(self, context: str, exc: BaseException):
        try:
            log_path = self.reports_dir / "ui_crash.log"
            with log_path.open("a", encoding="utf-8") as f:
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"[{context}] {type(exc).__name__}: {exc}\n")
                f.write(traceback.format_exc())
        except Exception:
            pass

    def _build_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        top_row = QHBoxLayout()
        title = QLabel("All PCs (SMB)")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        top_row.addWidget(title)
        top_row.addStretch()

        self.vision_box = QComboBox()
        self.vision_box.addItems(["Welding", "Lead"])
        self.vision_box.currentTextChanged.connect(self._on_vision_changed)
        top_row.addWidget(QLabel("Vision:"))
        top_row.addWidget(self.vision_box)

        self.export_btn = QPushButton("Export Summary CSV")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_summary)
        top_row.addWidget(self.export_btn)

        self.check_btn = QPushButton("Check All PCs")
        self.check_btn.clicked.connect(self.run_check_all)
        top_row.addWidget(self.check_btn)

        root.addLayout(top_row)

        self.status_label = QLabel("Press 'Check All PCs' to run. (Select a row to see details below.)")
        root.addWidget(self.status_label)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Status",
            "PC",
            "IP",
            "Recipe",
            "Folder",
            "FailCount",
            "Error (if any)",
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        self.table.cellDoubleClicked.connect(self.open_selected_details)
        self.table.itemSelectionChanged.connect(self._on_row_selected)

        self.detail_pane = MultiDetailPane(reports_dir=self.reports_dir)
        self.detail_pane.open_dialog_btn.clicked.connect(self._open_selected_details_dialog)

        split = QSplitter(Qt.Orientation.Vertical)
        split.addWidget(self.table)
        split.addWidget(self.detail_pane)
        split.setStretchFactor(0, 2)
        split.setStretchFactor(1, 3)

        root.addWidget(split)
        self.setLayout(root)

    def _vision_mode(self) -> str:
        return self.vision_box.currentText()

    def _kickout_dir(self) -> Path:
        return self.kickout_root / self._vision_mode()

    def _reset_screen(self):
        self._results = []
        self.table.setRowCount(0)
        self.export_btn.setEnabled(False)
        self.status_label.setText(
            f"Vision: {self._vision_mode()} — Press 'Check All PCs' to run. "
            f"(Select a row to see details below; double-click for dialog.)"
        )
        self.detail_pane.set_selection(None, None)

    def _load_pcs(self):
        try:
            self._pcs = load_pcs_config(self.pcs_json, self._vision_mode())
        except Exception as e:
            self._pcs = []
            QMessageBox.critical(self, "pcs.json error", str(e))

    def _set_busy(self, busy: bool):
        self.check_btn.setEnabled(not busy)
        self.vision_box.setEnabled(not busy)
        self.export_btn.setEnabled((not busy) and bool(self._results))

    def run_check_all(self):
        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "Busy", "A check is already running.")
            return

        if not self._pcs:
            self._load_pcs()
            if not self._pcs:
                return

        self._reset_screen()
        self._set_busy(True)

        self._worker = MultiPCCheckWorker(self._pcs, self._kickout_dir(), self._vision_mode())
        self._worker.progress.connect(self.status_label.setText)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_worker_failed(self, msg: str):
        self._set_busy(False)
        QMessageBox.critical(self, "Check Failed", msg)
        self.status_label.setText("Check failed.")
        self.detail_pane.set_selection(None, None)

    def _on_worker_finished(self, results: list):
        try:
            self._results = results
            self._render_results()
            self._set_busy(False)

            if self.table.rowCount() > 0:
                self.table.selectRow(0)
        except Exception as e:
            self._set_busy(False)
            self._log_crash("_on_worker_finished", e)
            QMessageBox.critical(
                self,
                "UI crashed while rendering results",
                "An internal error occurred while rendering results.\n"
                "Check reports/ui_crash.log for the full traceback."
            )
            self.status_label.setText("Render failed. See reports/ui_crash.log.")
            self.detail_pane.set_selection(None, None)

    def _on_vision_changed(self, _: str):
        self._reset_screen()
        self._load_pcs()

    def _safe_get(self, obj: Any, name: str, default=None):
        # tolerate dataclass or dict
        if hasattr(obj, name):
            return getattr(obj, name)
        if isinstance(obj, dict):
            return obj.get(name, default)
        return default

    def _render_results(self):
        try:
            self.table.setRowCount(0)

            pass_count = 0
            fail_count = 0
            err_count = 0

            for r in self._results:
                row = self.table.rowCount()
                self.table.insertRow(row)

                pc = self._safe_get(r, "pc", None)
                report = self._safe_get(r, "report", None)
                error = self._safe_get(r, "error", "")

                # if worker returned weird shape, show it as error instead of crashing
                if pc is None:
                    status = "ERROR"
                    err_count += 1
                    brush = QBrush(QColor(255, 243, 205))
                    pc_name = "<unknown>"
                    ip = ""
                    recipe = ""
                    folder = ""
                    fails = ""
                    err = f"Invalid result item type: {type(r)}"
                elif error or report is None:
                    status = "ERROR"
                    err_count += 1
                    brush = QBrush(QColor(255, 243, 205))
                    pc_name = getattr(pc, "key", str(pc))
                    ip = getattr(pc, "ip", "")
                    recipe = ""
                    folder = ""
                    fails = ""
                    err = error or "Unknown error"
                else:
                    rep = report
                    # rep.rows should exist; if not, don’t crash
                    rep_rows = getattr(rep, "rows", [])
                    fails_num = sum(1 for x in rep_rows if getattr(x, "is_pass", False) is False)

                    status = "PASS" if fails_num == 0 else "FAIL"
                    if fails_num == 0:
                        pass_count += 1
                        brush = QBrush(QColor(230, 255, 237))
                    else:
                        fail_count += 1
                        brush = QBrush(QColor(255, 235, 238))

                    pc_name = getattr(pc, "key", str(pc))
                    ip = getattr(pc, "ip", "")
                    recipe = getattr(rep, "recipe_name", "")
                    folder = getattr(rep, "recipe_id_3digit", "")
                    fails = str(fails_num)
                    err = ""

                items = [
                    QTableWidgetItem(status),
                    QTableWidgetItem(pc_name),
                    QTableWidgetItem(ip),
                    QTableWidgetItem(recipe),
                    QTableWidgetItem(folder),
                    QTableWidgetItem(fails),
                    QTableWidgetItem(err),
                ]
                for c, it in enumerate(items):
                    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    it.setBackground(brush)
                    self.table.setItem(row, c, it)

            self.table.resizeRowsToContents()
            self.status_label.setText(
                f"Done ({self._vision_mode()}). PASS={pass_count}, FAIL={fail_count}, ERROR={err_count}. "
                f"(Select a row to see details below; double-click for dialog.)"
            )
            self.export_btn.setEnabled(bool(self._results))

        except Exception as e:
            self._log_crash("_render_results", e)
            raise

    def _on_row_selected(self):
        # Never crash from selection changes
        try:
            row = self.table.currentRow()
            if row < 0 or row >= self.table.rowCount():
                self.detail_pane.set_selection(None, None)
                return

            pc_item = self.table.item(row, 1)
            if pc_item is None:
                self.detail_pane.set_selection(None, None)
                return

            pc_key = pc_item.text()
            pc = next((p for p in self._pcs if p.key == pc_key), None)
            if pc is None:
                self.detail_pane.set_selection(None, None)
                return

            res = next((x for x in self._results if self._safe_get(self._safe_get(x, "pc", None), "key", "") == pc_key), None)
            if res is None:
                self.detail_pane.set_selection(pc, None, error="No cached result found.")
                return

            err = self._safe_get(res, "error", "")
            rep = self._safe_get(res, "report", None)

            if err:
                self.detail_pane.set_selection(pc, None, error=err)
                return

            self.detail_pane.set_selection(pc, rep, error="")

        except Exception as e:
            self._log_crash("_on_row_selected", e)
            self.detail_pane.set_selection(None, None)

    def _open_selected_details_dialog(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.open_selected_details(row, 0)

    def export_summary(self):
        if not self._results:
            QMessageBox.information(self, "Export", "No results to export yet. Run 'Check All PCs' first.")
            return
        try:
            out_path = export_all_pcs_summary_csv(self._results, self.reports_dir)
            QMessageBox.information(self, "Export", f"Summary CSV saved:\n{out_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def open_selected_details(self, row: int, col: int):
        if row < 0 or row >= self.table.rowCount():
            return

        pc_item = self.table.item(row, 1)
        if pc_item is None:
            return
        pc_key = pc_item.text()

        pc = next((p for p in self._pcs if p.key == pc_key), None)
        if pc is None:
            QMessageBox.information(self, "Details", "PC not found in pcs.json.")
            return

        dlg = PCDetailsDialog(
            pc=pc,
            kickout_dir=self._kickout_dir(),
            reports_dir=self.reports_dir,
            vision_mode=self._vision_mode(),
            parent=self,
        )
        dlg.exec()