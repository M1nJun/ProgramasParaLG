from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QComboBox
)

from pc_config import load_pcs_config, PCEntry
from multi_pc_checker import PCCheckResult
from ui_pc_details import PCDetailsDialog
from workers import MultiPCCheckWorker
from multi_exporter_csv import export_all_pcs_summary_csv
from pc_config import load_pcs_config_nested


class MultiPCWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.base_dir = Path(__file__).resolve().parent
        self.reports_dir = self.base_dir / "reports"
        self.kickout_root = self.base_dir / "KickoutLists"
        self.pcs_json = self.base_dir / "pcs.json"

        self._pcs: list[PCEntry] = []
        self._results: list[PCCheckResult] = []
        self._worker: MultiPCCheckWorker | None = None

        self._build_ui()
        self._load_pcs()
        self._reset_screen()  # ✅ clean start

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
        self.vision_box.currentTextChanged.connect(lambda _: self._reset_screen())
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

        self.status_label = QLabel("Press 'Check All PCs' to run. (Double-click a row for details.)")
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
        root.addWidget(self.table)

        self.setLayout(root)

    def _vision_mode(self) -> str:
        return self.vision_box.currentText()

    def _kickout_dir(self) -> Path:
        return self.kickout_root / self._vision_mode()

    def _reset_screen(self):
        # Clean screen: no stale data shown
        self._results = []
        self.table.setRowCount(0)
        self.export_btn.setEnabled(False)
        self.status_label.setText(
            f"Vision: {self._vision_mode()} — Press 'Check All PCs' to run. (Double-click a row for details.)"
        )

    def _load_pcs(self):
        try:
            self._pcs = load_pcs_config_nested(self.pcs_json, self._vision_mode())
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

    def _on_worker_finished(self, results: list):
        self._results = results
        self._render_results()
        self._set_busy(False)

    def _render_results(self):
        self.table.setRowCount(0)

        pass_count = 0
        fail_count = 0
        err_count = 0

        for r in self._results:
            row = self.table.rowCount()
            self.table.insertRow(row)

            if r.error or r.report is None:
                status = "ERROR"
                err_count += 1
                brush = QBrush(QColor(255, 243, 205))
                recipe = ""
                folder = ""
                fails = ""
                err = r.error or "Unknown error"
            else:
                rep = r.report
                fails_num = sum(1 for x in rep.rows if not x.is_pass)
                status = "PASS" if fails_num == 0 else "FAIL"
                if fails_num == 0:
                    pass_count += 1
                    brush = QBrush(QColor(230, 255, 237))
                else:
                    fail_count += 1
                    brush = QBrush(QColor(255, 235, 238))
                recipe = rep.recipe_name
                folder = rep.recipe_id_3digit
                fails = str(fails_num)
                err = ""

            items = [
                QTableWidgetItem(status),
                QTableWidgetItem(r.pc.key),
                QTableWidgetItem(r.pc.ip),
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
            f"(Double-click a row for details.)"
        )
        self.export_btn.setEnabled(bool(self._results))

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
        pc_name_item = self.table.item(row, 1)
        if pc_name_item is None:
            return
        pc_key = pc_name_item.text()

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
