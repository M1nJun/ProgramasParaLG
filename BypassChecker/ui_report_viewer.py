from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QComboBox, QLineEdit
)

from checker import CheckReport, MeasureRow
from ui_filters import filter_rows
from report_exporter_csv import export_report_csv


class ReportViewerWidget(QWidget):
    """
    Reusable report viewer:
    - Default filter Fail
    - Search
    - Table (all occurrences)
    - Export CSV
    """
    def __init__(self, reports_dir: Path):
        super().__init__()
        self.reports_dir = reports_dir
        self._report: CheckReport | None = None

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # controls row
        row = QHBoxLayout()

        self.filter_box = QComboBox()
        self.filter_box.addItems(["All", "Fail", "Pass", "Missing", "Bypassed"])
        self.filter_box.setCurrentText("Fail")
        self.filter_box.currentTextChanged.connect(self._refresh_table)
        row.addWidget(QLabel("Filter:"))
        row.addWidget(self.filter_box)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search (master name or normalized key)…")
        self.search_box.textChanged.connect(self._refresh_table)
        self.search_box.setMinimumWidth(260)
        row.addWidget(self.search_box)

        row.addStretch()

        self.export_btn = QPushButton("Export CSV")
        self.export_btn.clicked.connect(self.export_csv)
        row.addWidget(self.export_btn)

        root.addLayout(row)

        # summary
        self.summary_label = QLabel("—")
        root.addWidget(self.summary_label)

        # table
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

    # -----------------------------
    # Report/row compatibility layer
    # -----------------------------
    def _report_schema(self, report: CheckReport) -> str:
        # checker.CheckReport has schema="welding"|"lead", but tolerate older objects.
        return str(getattr(report, "schema", "welding") or "welding").lower()

    def _required_counts(self, report: CheckReport) -> dict[str, int]:
        rc = getattr(report, "required_counts", None)
        return rc if isinstance(rc, dict) else {}

    def _get_required(self, report: CheckReport, *, legacy_attr: str | None, key: str) -> int:
        # Prefer legacy attribute if present (backward compatible)
        if legacy_attr and hasattr(report, legacy_attr):
            try:
                return int(getattr(report, legacy_attr))
            except Exception:
                pass
        # New schema
        try:
            return int(self._required_counts(report).get(key, 0))
        except Exception:
            return 0

    def _required_summary_text(self, report: CheckReport) -> str:
        schema = self._report_schema(report)

        if schema == "lead":
            anode = self._get_required(report, legacy_attr=None, key="Anode")
            cathode = self._get_required(report, legacy_attr=None, key="Cathode")
            shared = self._get_required(report, legacy_attr=None, key="Shared")
            return f"Required: anode={anode}, cathode={cathode}, shared={shared}"

        # default: welding (and also older builds that assumed upper/lower/both)
        upper = self._get_required(report, legacy_attr="required_upper", key="Upper")
        lower = self._get_required(report, legacy_attr="required_lower", key="Lower")
        both = self._get_required(report, legacy_attr="required_both", key="Both")
        return f"Required: upper={upper}, lower={lower}, both={both}"

    def _row_group_label(self, r: MeasureRow) -> str:
        # New name is r.group; older UI expected r.side.
        val = getattr(r, "side", None)
        if isinstance(val, str) and val.strip():
            return val
        val = getattr(r, "group", "")
        return val if isinstance(val, str) else ""

    # -----------------------------
    # Main API
    # -----------------------------
    def set_report(self, report: CheckReport | None):
        self._report = report
        if report is None:
            self.summary_label.setText("No report.")
            self.table.setRowCount(0)
            return

        fail_count = sum(1 for r in report.rows if not r.is_pass)
        missing_count = sum(1 for r in report.rows if r.is_missing)
        bypassed_count = sum(1 for r in report.rows if r.has_bypassed)

        self.summary_label.setText(
            f"Recipe: {report.recipe_name} (folder {report.recipe_id_3digit}) | "
            f"{self._required_summary_text(report)} | "
            f"Rows: {len(report.rows)}  Fail: {fail_count} (missing={missing_count}, bypassed={bypassed_count})"
        )
        self._refresh_table()

    def _row_brush(self, r: MeasureRow) -> QBrush:
        if r.is_pass:
            return QBrush(QColor(230, 255, 237))  # light green
        return QBrush(QColor(255, 235, 238))      # light red

    def _refresh_table(self):
        report = self._report
        if report is None:
            return

        mode = self.filter_box.currentText()
        query = self.search_box.text()

        rows_sorted = sorted(report.rows, key=lambda x: x.normalized_key)
        rows_filtered = filter_rows(rows_sorted, mode=mode, query=query)

        self.table.setRowCount(0)
        for r in rows_filtered:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)

            status_text = "PASS" if r.is_pass else "FAIL"
            occ_text = "\n".join(
                f"{o.item_tag} | {o.name} | bypass={str(o.bypass).lower()}"
                for o in r.occurrences
            ) if r.occurrences else "(no occurrences found)"

            items = [
                QTableWidgetItem(status_text),
                QTableWidgetItem(r.display_name),
                QTableWidgetItem(self._row_group_label(r)),
                QTableWidgetItem(r.normalized_key),
                QTableWidgetItem(str(r.expected_count)),
                QTableWidgetItem(str(r.found_count)),
                QTableWidgetItem(occ_text),
            ]

            brush = self._row_brush(r)
            for col, it in enumerate(items):
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                it.setBackground(brush)
                self.table.setItem(row_idx, col, it)

        self.table.resizeRowsToContents()

    def export_csv(self):
        if self._report is None:
            QMessageBox.information(self, "Export", "No report to export yet.")
            return
        try:
            out_path = export_report_csv(self._report, self.reports_dir, show_all_occurrences=True)
            QMessageBox.information(self, "Export", f"CSV saved:\n{out_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))