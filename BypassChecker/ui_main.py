from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFrame,
    QComboBox,
    QLineEdit,
)

from preference_reader import read_recipe_info
from recipe_locator import locate_recipe_paths
from recipe_parser import parse_recipe_measures
from kickout_loader import load_kickout_list_xlsx
from checker import check_kickout, CheckReport, MeasureRow
from ui_filters import filter_rows
from report_exporter_csv import export_report_csv


class BypassCheckerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bypass Checker (Welding Vision)")

        self.base_dir = Path(__file__).resolve().parent
        self.kickout_dir = self.base_dir / "KickoutLists" / "Welding"
        self.reports_dir = self.base_dir / "reports"
        self.preference_ini = Path(r"C:\VisionPC\Setting\Preference.ini")

        self._last_report: CheckReport | None = None

        self._build_ui()
        self.run_check()

    def _build_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        top_row = QHBoxLayout()
        self.title_label = QLabel("Bypass Checker")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        top_row.addWidget(self.title_label)

        top_row.addStretch()

        self.filter_box = QComboBox()
        self.filter_box.addItems(["All", "Fail", "Pass", "Missing", "Bypassed"])
        self.filter_box.setCurrentText("Fail")  # default filter = Fail
        self.filter_box.currentTextChanged.connect(self._refresh_table_from_report)
        top_row.addWidget(QLabel("Filter:"))
        top_row.addWidget(self.filter_box)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search (master name or normalized key)…")
        self.search_box.textChanged.connect(self._refresh_table_from_report)
        self.search_box.setMinimumWidth(260)
        top_row.addWidget(self.search_box)

        self.export_btn = QPushButton("Export CSV")
        self.export_btn.clicked.connect(self.export_report)
        top_row.addWidget(self.export_btn)

        self.refresh_btn = QPushButton("Re-check")
        self.refresh_btn.clicked.connect(self.run_check)
        top_row.addWidget(self.refresh_btn)

        root.addLayout(top_row)

        # Status panel
        self.status_frame = QFrame()
        self.status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_layout = QVBoxLayout()
        status_layout.setContentsMargins(12, 12, 12, 12)
        status_layout.setSpacing(6)

        self.status_big = QLabel("—")
        self.status_big.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_big.setStyleSheet("font-size: 22px; font-weight: 700;")
        status_layout.addWidget(self.status_big)

        self.recipe_info_label = QLabel("Recipe: —")
        status_layout.addWidget(self.recipe_info_label)

        self.summary_label = QLabel("Summary: —")
        status_layout.addWidget(self.summary_label)

        self.status_frame.setLayout(status_layout)
        root.addWidget(self.status_frame)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Status",
            "Measure (Master)",
            "Side",
            "Normalized Key",
            "Expected",
            "Found",
            "Occurrences (all)",
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setWordWrap(True)

        root.addWidget(self.table)

        self.setLayout(root)
        self.resize(1280, 700)

    def _set_status(self, ok: bool):
        if ok:
            self.status_big.setText("PASS ✅")
            self.status_big.setStyleSheet("font-size: 22px; font-weight: 700; color: #0a7d2c;")
        else:
            self.status_big.setText("FAIL ❌")
            self.status_big.setStyleSheet("font-size: 22px; font-weight: 700; color: #b00020;")

    def run_check(self):
        try:
            info = read_recipe_info(self.preference_ini)
            paths = locate_recipe_paths(info)
            measures = parse_recipe_measures(paths.recipe_file)

            kickout_path = self.kickout_dir / f"{info.recipe_name}.xlsx"
            kickout = load_kickout_list_xlsx(kickout_path, sheet_name="Welding")

            report = check_kickout(
                measures=measures,
                kickout=kickout,
                recipe_name=info.recipe_name,
                recipe_id_3digit=info.recipe_id_3digit,
                kickout_filename=kickout_path.name,
            )

            self._last_report = report
            self._update_status_labels(report)
            self._refresh_table_from_report()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self._last_report = None
            self._set_status(False)
            self.recipe_info_label.setText("Recipe: —")
            self.summary_label.setText("Summary: —")
            self.table.setRowCount(0)

    def _update_status_labels(self, report: CheckReport):
        fail_count = sum(1 for r in report.rows if not r.is_pass)
        missing_count = sum(1 for r in report.rows if r.is_missing)
        bypassed_count = sum(1 for r in report.rows if r.has_bypassed)

        self._set_status(fail_count == 0)
        self.recipe_info_label.setText(
            f"Recipe: {report.recipe_name} (folder {report.recipe_id_3digit})   Kickout: {report.kickout_filename}"
        )
        self.summary_label.setText(
            f"Required: upper={report.required_upper}, lower={report.required_lower}, both={report.required_both} | "
            f"Rows: {len(report.rows)}  Fail: {fail_count} (missing={missing_count}, bypassed={bypassed_count})"
        )

        warn_parts = []
        if report.master_upper_duplicates:
            warn_parts.append(f"Upper dupes: {len(report.master_upper_duplicates)}")
        if report.master_lower_duplicates:
            warn_parts.append(f"Lower dupes: {len(report.master_lower_duplicates)}")

        self.title_label.setText(
            "Bypass Checker" if not warn_parts else f"Bypass Checker — Master warnings ({', '.join(warn_parts)})"
        )

    def _row_brush(self, r: MeasureRow) -> QBrush | None:
        if r.is_pass:
            return QBrush(QColor(230, 255, 237))  # light green
        return QBrush(QColor(255, 235, 238))      # light red

    def _refresh_table_from_report(self):
        report = self._last_report
        if report is None:
            return

        mode = self.filter_box.currentText()
        query = self.search_box.text()

        rows_sorted = sorted(report.rows, key=lambda x: x.normalized_key)
        rows_filtered = filter_rows(rows_sorted, mode=mode, query=query)
        self._fill_table(rows_filtered)

    def _fill_table(self, rows: list[MeasureRow]):
        self.table.setRowCount(0)

        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            status_text = "PASS" if r.is_pass else "FAIL"

            if r.occurrences:
                occ_text = "\n".join(
                    f"{o.item_tag} | {o.name} | bypass={str(o.bypass).lower()}"
                    for o in r.occurrences
                )
            else:
                occ_text = "(no occurrences found)"

            items = [
                QTableWidgetItem(status_text),
                QTableWidgetItem(r.display_name),
                QTableWidgetItem(r.side),
                QTableWidgetItem(r.normalized_key),
                QTableWidgetItem(str(r.expected_count)),
                QTableWidgetItem(str(r.found_count)),
                QTableWidgetItem(occ_text),
            ]

            brush = self._row_brush(r)
            for col, item in enumerate(items):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if brush is not None:
                    item.setBackground(brush)
                self.table.setItem(row, col, item)

        self.table.resizeRowsToContents()

    def export_report(self):
        report = self._last_report
        if report is None:
            QMessageBox.information(self, "Export", "No report to export yet.")
            return

        try:
            out_path = export_report_csv(report, self.reports_dir, show_all_occurrences=True)
            QMessageBox.information(self, "Export", f"CSV saved:\n{out_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))
