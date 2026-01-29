
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Tuple

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QGroupBox, QFormLayout,
    QMessageBox, QCheckBox, QComboBox
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


class SearchWorker(QThread):
    progress = pyqtSignal(int, int)   # done, total
    row_result = pyqtSignal(dict)     # per-cell result
    log = pyqtSignal(str)
    finished_ok = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(
        self,
        drive_letter: str,
        sub_path: str,
        date_ymd: Tuple[str, str, str],
        cell_ids: List[str],
        choose_latest_only: bool,
        do_copy: bool,
        out_dir: Optional[Path],
        parent=None
    ):
        super().__init__(parent)
        self.drive_letter = (drive_letter or "E").strip().upper().replace(":", "")
        self.sub_path = sub_path.strip().lstrip("\\/")
        self.yyyy, self.mm, self.dd = date_ymd
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
            self.log.emit(f"Date: {self.yyyy}-{self.mm}-{self.dd}")
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

                matches = search_matches_for_cell(base_dir, self.yyyy, self.mm, self.dd, cell_id)

                if not matches:
                    self.row_result.emit({
                        "cell_id": cell_id,
                        "status": "NOT FOUND",
                        "match_count": 0,
                        "category": "",
                        "folder": "",
                        "img0": "",
                        "img1": "",
                        "copied0": "",
                        "copied1": "",
                    })
                else:
                    best = choose_best_match(matches)
                    to_show = best if (self.choose_latest_only and best) else (best or matches[0])

                    copied0 = copied1 = ""
                    if self.do_copy and to_show:
                        d0, d1 = copy_images(to_show, self.out_dir)
                        copied0 = str(d0) if d0 else ""
                        copied1 = str(d1) if d1 else ""

                    self.row_result.emit({
                        "cell_id": cell_id,
                        "status": "FOUND",
                        "match_count": len(matches),
                        "category": str(to_show.category_dir),
                        "folder": str(to_show.folder),
                        "img0": str(to_show.img0) if to_show.img0 else "",
                        "img1": str(to_show.img1) if to_show.img1 else "",
                        "copied0": copied0,
                        "copied1": copied1,
                    })

                done += 1
                self.progress.emit(done, total)

            self.finished_ok.emit()

        except Exception as e:
            self.failed.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cell Image Finder (JF2)")

        self.worker: Optional[SearchWorker] = None

        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)

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

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(self.date_edit.date().currentDate())
        form.addRow(QLabel("Date"), self.date_edit)

        self.cells_edit = QTextEdit()
        self.cells_edit.setPlaceholderText("Enter cell IDs separated by space, newline, or comma.")
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
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Cell ID", "Status", "Matches", "Category Dir", "Folder",
            "IMG 0_2", "IMG 1_2", "Copied Folder"
        ])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        for c in range(3, 8):
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

        self.resize(1200, 820)

    def browse_out_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d:
            self.out_dir_edit.setText(d)

    def append_log(self, msg: str):
        self.log_box.append(msg)

    def clear_results(self):
        self.table.setRowCount(0)

    def add_row(self, result: dict):
        row = self.table.rowCount()
        self.table.insertRow(row)

        def put(col: int, val: str):
            item = QTableWidgetItem(val)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, col, item)

        put(0, result.get("cell_id", ""))
        put(1, result.get("status", ""))
        put(2, str(result.get("match_count", 0)))
        put(3, result.get("category", ""))
        put(4, result.get("folder", ""))
        put(5, result.get("img0", ""))
        put(6, result.get("img1", ""))

        copied_folder = ""
        if result.get("copied0") or result.get("copied1"):
            any_copy = result.get("copied0") or result.get("copied1")
            copied_folder = str(Path(any_copy).parent)
        put(7, copied_folder)

        status = result.get("status", "")
        if status == "FOUND":
            for c in range(self.table.columnCount()):
                it = self.table.item(row, c)
                if it:
                    it.setBackground(Qt.GlobalColor.green)
        elif status == "NOT FOUND":
            for c in range(self.table.columnCount()):
                it = self.table.item(row, c)
                if it:
                    it.setBackground(Qt.GlobalColor.yellow)

    def run_search(self):
        drive = self.drive_box.currentText().strip() or "E"
        sub_path = self.sub_path_edit.text().strip() or r"Files\Image\JF2"

        date_q = self.date_edit.date()
        date_str = f"{date_q.year():04d}-{date_q.month():02d}-{date_q.day():02d}"

        cell_ids = normalize_cell_ids(self.cells_edit.toPlainText())
        if not cell_ids:
            QMessageBox.warning(self, "Missing Cell IDs", "Please enter at least one cell ID.")
            return

        try:
            ymd = parse_date(date_str)
        except Exception as e:
            QMessageBox.critical(self, "Bad Date", str(e))
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
            date_ymd=ymd,
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
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
