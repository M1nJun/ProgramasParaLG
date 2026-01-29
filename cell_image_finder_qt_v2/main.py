
from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QGroupBox, QFormLayout,
    QMessageBox, QCheckBox, QComboBox, QTabWidget, QFrame
)

from finder import parse_date, search_matches_for_cell, choose_best_match, copy_images


def normalize_cell_ids(text: str) -> List[str]:
    raw = []
    for part in text.replace(",", " ").split():
        p = part.strip()
        if p:
            raw.append(p)
    seen = set()
    out = []
    for x in raw:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def parse_date_lines(text: str) -> List[Tuple[str, str, str]]:
    """
    Accepts lines like:
      2026-01-13
      2026/01/17
    Ignores blank lines and comments starting with '#'.
    Returns unique dates in the order given.
    """
    out: List[Tuple[str, str, str]] = []
    seen = set()
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        ymd = parse_date(s)
        if ymd not in seen:
            seen.add(ymd)
            out.append(ymd)
    return out

def iter_date_range(start_ymd: Tuple[str, str, str], end_ymd: Tuple[str, str, str]) -> List[Tuple[str, str, str]]:
    ys, ms, ds = start_ymd
    ye, me, de = end_ymd
    start = date(int(ys), int(ms), int(ds))
    end = date(int(ye), int(me), int(de))
    if end < start:
        raise ValueError("End date must be the same as or after Start date.")

    out = []
    cur = start
    while cur <= end:
        out.append((f"{cur.year:04d}", f"{cur.month:02d}", f"{cur.day:02d}"))
        cur += timedelta(days=1)
    return out

def qdate_to_ymd(qd: QDate) -> Tuple[str, str, str]:
    return (f"{qd.year():04d}", f"{qd.month():02d}", f"{qd.day():02d}")

@dataclass
class RowPayload:
    cell_id: str
    status: str
    match_count: int
    chosen_date: str
    category: str
    folder: str
    img0: str
    img1: str
    copied_folder: str


class SearchWorker(QThread):
    progress = pyqtSignal(int, int)   # done, total
    row_result = pyqtSignal(object)   # RowPayload
    log = pyqtSignal(str)
    finished_ok = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(
        self,
        drive_letter: str,
        sub_path: str,
        dates_to_search: List[Tuple[str, str, str]],
        cell_ids: List[str],
        choose_latest_only: bool,
        do_copy: bool,
        out_dir: Optional[Path],
        parent=None
    ):
        super().__init__(parent)
        self.drive_letter = (drive_letter or "E").strip().upper().replace(":", "")
        self.sub_path = sub_path.strip().lstrip("\\/")
        self.dates_to_search = dates_to_search
        self.cell_ids = cell_ids
        self.choose_latest_only = choose_latest_only
        self.do_copy = do_copy
        self.out_dir = out_dir
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            base_dir = Path(f"{self.drive_letter}:\\") / self.sub_path
            if not base_dir.exists():
                self.failed.emit(f"Base directory does not exist:\n{base_dir}")
                return

            total = len(self.cell_ids)
            done = 0

            self.log.emit(f"Base: {base_dir}")
            self.log.emit(f"Dates: {len(self.dates_to_search)} day(s)")
            self.log.emit(f"Cells: {total}")

            if self.do_copy:
                if not self.out_dir:
                    self.failed.emit("Copy is enabled but output folder is not set.")
                    return
                self.out_dir.mkdir(parents=True, exist_ok=True)
                self.log.emit(f"Copy output: {self.out_dir}")

            for cell_id in self.cell_ids:
                if self._stop:
                    self.log.emit("Stopped by user.")
                    return

                all_matches = []
                for (yyyy, mm, dd) in self.dates_to_search:
                    if self._stop:
                        self.log.emit("Stopped by user.")
                        return
                    matches = search_matches_for_cell(base_dir, yyyy, mm, dd, cell_id)
                    all_matches.extend(matches)

                if not all_matches:
                    payload = RowPayload(
                        cell_id=cell_id,
                        status="NOT FOUND",
                        match_count=0,
                        chosen_date="",
                        category="",
                        folder="",
                        img0="",
                        img1="",
                        copied_folder="",
                    )
                    self.row_result.emit(payload)
                else:
                    best = choose_best_match(all_matches)
                    to_show = best if (self.choose_latest_only and best) else (best or all_matches[0])

                    copied_folder = ""
                    if self.do_copy and to_show:
                        d0, d1 = copy_images(to_show, self.out_dir)
                        # copied folder based on any copied path
                        any_copy = d0 or d1
                        copied_folder = str(any_copy.parent) if any_copy else ""

                    chosen_date = ""
                    if to_show and to_show.timestamp_key:
                        # timestamp_key starts with YYYYMMDD
                        chosen_date = to_show.timestamp_key.split("_")[0]  # YYYYMMDD

                    payload = RowPayload(
                        cell_id=cell_id,
                        status="FOUND",
                        match_count=len(all_matches),
                        chosen_date=chosen_date,
                        category=str(to_show.category_dir),
                        folder=str(to_show.folder),
                        img0=str(to_show.img0) if to_show.img0 else "",
                        img1=str(to_show.img1) if to_show.img1 else "",
                        copied_folder=copied_folder,
                    )
                    self.row_result.emit(payload)

                done += 1
                self.progress.emit(done, total)

            self.finished_ok.emit()

        except Exception as e:
            self.failed.emit(str(e))


def apply_modern_styles(app: QApplication):
    # Fusion style + a lightweight modern stylesheet (rounded corners, subtle borders)
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QWidget { font-size: 12px; }
        QMainWindow { background: #0f1115; }
        QWidget#centralWidget { background: #0f1115; color: #e6e6e6; }

        QGroupBox {
            border: 1px solid #2a2f3a;
            border-radius: 12px;
            margin-top: 10px;
            padding: 10px;
            background: #141824;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: #cfd8ff;
        }

        QLineEdit, QTextEdit, QDateEdit, QComboBox {
            background: #0f1115;
            border: 1px solid #2a2f3a;
            border-radius: 10px;
            padding: 8px;
            color: #e6e6e6;
        }

        QComboBox::drop-down { border: 0px; width: 24px; }
        QComboBox QAbstractItemView {
            background: #0f1115;
            selection-background-color: #2c5cff;
            border: 1px solid #2a2f3a;
        }

        QPushButton {
            background: #2c5cff;
            border: none;
            border-radius: 10px;
            padding: 10px 14px;
            color: white;
            font-weight: 600;
        }
        QPushButton:disabled { background: #3a4256; color: #b4b4b4; }
        QPushButton#secondaryBtn { background: #2a2f3a; }

        QTabWidget::pane {
            border: 1px solid #2a2f3a;
            border-radius: 12px;
            top: -1px;
            background: #141824;
        }
        QTabBar::tab {
            background: #0f1115;
            color: #b9c1d6;
            border: 1px solid #2a2f3a;
            padding: 8px 12px;
            margin-right: 6px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        }
        QTabBar::tab:selected {
            background: #141824;
            color: #e6e6e6;
            border-bottom-color: #141824;
        }

        QProgressBar {
            background: #141824;
            border: 1px solid #2a2f3a;
            border-radius: 10px;
            text-align: center;
            color: #e6e6e6;
            padding: 3px;
        }
        QProgressBar::chunk { background: #2c5cff; border-radius: 8px; }

        QTableWidget {
            background: #0f1115;
            gridline-color: #2a2f3a;
            border: 1px solid #2a2f3a;
            border-radius: 12px;
            color: #e6e6e6;
        }
        QHeaderView::section {
            background: #141824;
            color: #cfd8ff;
            border: none;
            padding: 8px;
        }
        QTextEdit { font-family: Consolas, "Courier New", monospace; }
    """)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cell Image Finder (JF2)")

        self.worker: Optional[SearchWorker] = None

        root = QWidget()
        root.setObjectName("centralWidget")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)

        # Header
        header = QHBoxLayout()
        title = QLabel("Cell Image Finder")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Search NG / DL_CANDIDATE / DL_OK by Cell ID")
        subtitle.setStyleSheet("color: #aab3c9;")
        header_col = QVBoxLayout()
        header_col.addWidget(title)
        header_col.addWidget(subtitle)
        header.addLayout(header_col)
        header.addStretch(1)
        outer.addLayout(header)

        # Inputs
        inputs = QGroupBox("Inputs")
        form = QFormLayout(inputs)

        self.drive_box = QComboBox()
        self.drive_box.setEditable(True)
        self.drive_box.addItems(["E", "D", "F", "C"])
        self.drive_box.setCurrentText("E")
        form.addRow(QLabel("Drive"), self.drive_box)

        self.sub_path_edit = QLineEdit(r"Files\Image\JF2")
        form.addRow(QLabel("Sub path"), self.sub_path_edit)

        # Date tab widget (Option A + B)
        self.date_tabs = QTabWidget()

        # Tab A: Range
        range_tab = QWidget()
        range_layout = QFormLayout(range_tab)
        self.start_date = QDateEdit()
        self.end_date = QDateEdit()
        for w in (self.start_date, self.end_date):
            w.setCalendarPopup(True)
            w.setDisplayFormat("yyyy-MM-dd")
            w.setDate(QDate.currentDate())
        range_layout.addRow(QLabel("Start"), self.start_date)
        range_layout.addRow(QLabel("End"), self.end_date)
        self.date_tabs.addTab(range_tab, "Date Range")

        # Tab B: List
        list_tab = QWidget()
        list_layout = QVBoxLayout(list_tab)
        hint = QLabel("Enter dates (one per line). Formats: YYYY-MM-DD or YYYY/MM/DD. Lines starting with # are ignored.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #aab3c9;")
        self.date_list = QTextEdit()
        self.date_list.setPlaceholderText("2026-01-13\n2026-01-17\n# 2026-01-20 (commented out)")
        self.date_list.setFixedHeight(90)
        list_layout.addWidget(hint)
        list_layout.addWidget(self.date_list)
        self.date_tabs.addTab(list_tab, "Date List")

        form.addRow(QLabel("Dates"), self.date_tabs)

        # Cell IDs
        self.cells_edit = QTextEdit()
        self.cells_edit.setPlaceholderText("Enter cell IDs separated by space, newline, or comma.\nExample:\nd5B1K03556\nc5CMK04107")
        self.cells_edit.setFixedHeight(110)
        form.addRow(QLabel("Cell IDs"), self.cells_edit)

        outer.addWidget(inputs)

        # Options
        opts = QGroupBox("Options")
        opts_layout = QVBoxLayout(opts)

        self.latest_only_cb = QCheckBox("Choose latest match only (recommended)")
        self.latest_only_cb.setChecked(True)

        self.copy_cb = QCheckBox("Copy found images to output folder")
        self.copy_cb.setChecked(False)

        out_row = QHBoxLayout()
        self.out_dir_edit = QLineEdit()
        self.out_dir_edit.setPlaceholderText("Output folder (required if copy is enabled)")
        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.setObjectName("secondaryBtn")
        self.browse_btn.clicked.connect(self.browse_out_dir)
        out_row.addWidget(self.out_dir_edit, 1)
        out_row.addWidget(self.browse_btn)

        opts_layout.addWidget(self.latest_only_cb)
        opts_layout.addWidget(self.copy_cb)
        opts_layout.addLayout(out_row)

        outer.addWidget(opts)

        # Buttons + progress
        btn_row = QHBoxLayout()
        self.run_btn = QPushButton("Run Search")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("secondaryBtn")
        self.stop_btn.setEnabled(False)
        self.run_btn.clicked.connect(self.run_search)
        self.stop_btn.clicked.connect(self.stop_search)
        btn_row.addWidget(self.run_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addStretch(1)

        self.progress = QProgressBar()
        self.progress.setValue(0)

        outer.addLayout(btn_row)
        outer.addWidget(self.progress)

        # Results table
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "Cell ID", "Status", "Matches", "Chosen Date", "Category Dir", "Folder",
            "IMG 0_2", "IMG 1_2", "Copied Folder"
        ])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        for c in range(4, 9):
            hdr.setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        outer.addWidget(self.table, 1)

        # Log
        outer.addWidget(QLabel("Log"))
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(140)
        outer.addWidget(self.log_box)

        self.resize(1280, 900)

    def browse_out_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d:
            self.out_dir_edit.setText(d)

    def append_log(self, msg: str):
        self.log_box.append(msg)

    def clear_results(self):
        self.table.setRowCount(0)

    def add_row(self, payload: RowPayload):
        row = self.table.rowCount()
        self.table.insertRow(row)

        def put(col: int, val: str):
            item = QTableWidgetItem(val)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, col, item)

        put(0, payload.cell_id)
        put(1, payload.status)
        put(2, str(payload.match_count))
        put(3, payload.chosen_date)
        put(4, payload.category)
        put(5, payload.folder)
        put(6, payload.img0)
        put(7, payload.img1)
        put(8, payload.copied_folder)

        if payload.status == "FOUND":
            # subtle green tint (using selection color isn't allowed here; set background per cell)
            for c in range(self.table.columnCount()):
                it = self.table.item(row, c)
                if it:
                    it.setBackground(Qt.GlobalColor.darkGreen)
        elif payload.status == "NOT FOUND":
            for c in range(self.table.columnCount()):
                it = self.table.item(row, c)
                if it:
                    it.setBackground(Qt.GlobalColor.darkYellow)

    def get_dates_to_search(self) -> List[Tuple[str, str, str]]:
        idx = self.date_tabs.currentIndex()

        if idx == 0:
            # Date Range
            start = qdate_to_ymd(self.start_date.date())
            end = qdate_to_ymd(self.end_date.date())
            return iter_date_range(start, end)

        # Date List
        dates = parse_date_lines(self.date_list.toPlainText())
        if not dates:
            raise ValueError("Date List is empty. Please enter at least one date.")
        return dates

    def run_search(self):
        drive = self.drive_box.currentText().strip() or "E"
        sub_path = self.sub_path_edit.text().strip() or r"Files\Image\JF2"

        cell_ids = normalize_cell_ids(self.cells_edit.toPlainText())
        if not cell_ids:
            QMessageBox.warning(self, "Missing Cell IDs", "Please enter at least one cell ID.")
            return

        try:
            dates_to_search = self.get_dates_to_search()
        except Exception as e:
            QMessageBox.critical(self, "Bad Dates", str(e))
            return

        do_copy = self.copy_cb.isChecked()
        out_dir = None
        if do_copy:
            out_text = self.out_dir_edit.text().strip()
            if not out_text:
                QMessageBox.warning(self, "Missing Output Folder", "Copy is enabled. Please choose an output folder.")
                return
            out_dir = Path(out_text)

        self.clear_results()
        self.log_box.clear()
        self.progress.setMaximum(len(cell_ids))
        self.progress.setValue(0)

        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self.worker = SearchWorker(
            drive_letter=drive,
            sub_path=sub_path,
            dates_to_search=dates_to_search,
            cell_ids=cell_ids,
            choose_latest_only=self.latest_only_cb.isChecked(),
            do_copy=do_copy,
            out_dir=out_dir,
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.row_result.connect(self.add_row)
        self.worker.log.connect(self.append_log)
        self.worker.finished_ok.connect(self.on_done)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

        # Log summary
        self.append_log(f"Searching {len(dates_to_search)} day(s) for {len(cell_ids)} cell(s)…")

    def stop_search(self):
        if self.worker:
            self.worker.stop()
            self.append_log("Stop requested…")
            self.stop_btn.setEnabled(False)

    def on_progress(self, done: int, total: int):
        self.progress.setValue(done)
        self.progress.setFormat(f"{done}/{total}")

    def on_done(self):
        self.append_log("Done.")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.worker = None

    def on_failed(self, msg: str):
        QMessageBox.critical(self, "Error", msg)
        self.append_log(f"ERROR: {msg}")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.worker = None


def main():
    app = QApplication(sys.argv)
    apply_modern_styles(app)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
