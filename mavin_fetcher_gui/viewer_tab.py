from __future__ import annotations

from pathlib import Path
from typing import Optional, List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QLineEdit, QComboBox, QMessageBox
)

from mavin_fetcher.view_index import ViewIndex, resolve_folder_for_class_key, OccurrenceItem
from mavin_fetcher.labeling.pathing import human_root_from_output
from mavin_fetcher.labeling.label_engine import apply_label, undo as undo_label
from mavin_fetcher.labeling.types import LabelAction

from .image_preview import ImagePreview
from .log_widget import LogWidget
from .session_manager import SessionManager
from .viewer_worker import ViewerWorker, ViewerBuildConfig
from .status_bar import StatusBarLabel


class ViewerTab(QWidget):
    def __init__(self, session: SessionManager):
        super().__init__()
        self.session = session

        self._index: Optional[ViewIndex] = None
        self._worker: Optional[ViewerWorker] = None

        # undo stack (move-mode)
        self._undo_stack: List[LabelAction] = []

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ✅ Status bar at top (auto clears)
        self.status = StatusBarLabel(clear_ms=2000)
        root.addWidget(self.status)

        # Top bar
        top = QHBoxLayout()
        self.out_label = QLabel("Output: -")
        self.human_label = QLabel("HumanReview: -")
        self.refresh_btn = QPushButton("Refresh Index")
        top.addWidget(self.out_label)
        top.addSpacing(12)
        top.addWidget(self.human_label)
        top.addStretch(1)
        top.addWidget(self.refresh_btn)
        root.addLayout(top)

        # Filters
        filt = QHBoxLayout()
        self.region_filter = QComboBox()
        self.region_filter.addItems(["All", "LOWER_B_L", "LOWER_B_R", "UPPER_B_L", "UPPER_B_R"])
        self.map_filter = QComboBox()
        self.map_filter.addItems(["SourceMap", "ActiveMap"])  # default SourceMap
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search cell contains...")
        filt.addWidget(QLabel("Region:"))
        filt.addWidget(self.region_filter)
        filt.addSpacing(10)
        filt.addWidget(QLabel("Map:"))
        filt.addWidget(self.map_filter)
        filt.addSpacing(10)
        filt.addWidget(self.search)
        root.addLayout(filt)

        # Main area (3 columns)
        main = QHBoxLayout()

        self.class_list = QListWidget()
        self.class_list.setMinimumWidth(220)
        main.addWidget(self.class_list)

        self.occ_list = QListWidget()
        self.occ_list.setMinimumWidth(360)
        main.addWidget(self.occ_list)

        self.preview = ImagePreview()
        main.addWidget(self.preview, stretch=1)

        root.addLayout(main)

        root.addWidget(QLabel("Viewer Log:"))
        self.log = LogWidget()
        self.log.setMinimumHeight(120)
        root.addWidget(self.log)

        # wiring
        self.refresh_btn.clicked.connect(self.rebuild_index)

        self.class_list.currentItemChanged.connect(lambda *_: self._rebuild_occ_list())
        self.region_filter.currentIndexChanged.connect(lambda *_: self._rebuild_occ_list())
        self.search.textChanged.connect(lambda *_: self._rebuild_occ_list())
        self.map_filter.currentIndexChanged.connect(lambda *_: self._update_preview_for_selected())

        self.occ_list.currentItemChanged.connect(lambda *_: self._update_preview_for_selected())

        self.session.changed.connect(lambda *_: self._sync_paths())

        # hotkeys
        self._install_hotkeys()

        # initial
        self._sync_paths()
        self.rebuild_index()

    def _sync_paths(self) -> None:
        out_dir = (self.session.state.out_dir or "").strip()
        self.out_label.setText(f"Output: {out_dir}")
        if out_dir:
            human_root = human_root_from_output(Path(out_dir))
            self.human_label.setText(f"HumanReview: {human_root}")
        else:
            self.human_label.setText("HumanReview: -")

    def _install_hotkeys(self) -> None:
        # WidgetWithChildrenShortcut = active anywhere in this tab
        def mk(seq: str, fn):
            sc = QShortcut(QKeySequence(seq), self)
            sc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            sc.activated.connect(fn)
            return sc

        self._hk_realng = mk("1", lambda: self._hotkey_label("RealNG"))
        self._hk_overkill = mk("2", lambda: self._hotkey_label("Overkill"))
        self._hk_undo = mk("Ctrl+Z", self._hotkey_undo)

    def _focus_is_typing(self) -> bool:
        w = self.window().focusWidget()
        return isinstance(w, QLineEdit)

    # ---- External hook (from Summary click) ----
    def show_class_key(self, class_key: str) -> None:
        if not self._index:
            QMessageBox.information(self, "Viewer", "Index not ready yet. Click Refresh Index.")
            return
        folder = resolve_folder_for_class_key(self._index, class_key)
        if not folder:
            QMessageBox.information(
                self, "Viewer",
                f"Class folder not found for '{class_key}'.\nFetch images first (or Refresh Index)."
            )
            return
        for i in range(self.class_list.count()):
            if self.class_list.item(i).text() == folder:
                self.class_list.setCurrentRow(i)
                return

    # ---- Index building ----
    def rebuild_index(self) -> None:
        if self._worker and self._worker.isRunning():
            return

        out_dir = (self.session.state.out_dir or "").strip()
        if not out_dir:
            QMessageBox.warning(self, "Missing output", "Please set Output folder in Session.")
            return

        self.status.set_info("Rebuilding viewer index…")
        self.log.append_line("[INFO] Rebuilding index...")
        self.class_list.clear()
        self.occ_list.clear()
        self.preview.set_image(None)
        self._index = None

        self._worker = ViewerWorker(ViewerBuildConfig(out_dir=out_dir))
        self._worker.log.connect(self.log.append_line)
        self._worker.done.connect(self._on_index_ready)
        self._worker.failed.connect(self._on_index_failed)
        self._worker.start()

    def _on_index_failed(self, msg: str) -> None:
        self.status.set_error("Index build failed.")
        QMessageBox.warning(self, "Viewer error", msg)

    def _on_index_ready(self, idx_obj: object) -> None:
        if not isinstance(idx_obj, ViewIndex):
            self.status.set_error("Index build failed.")
            QMessageBox.warning(self, "Viewer error", "Invalid index object returned.")
            return

        self._index = idx_obj
        self.class_list.clear()

        for folder_name in sorted(self._index.classes.keys()):
            self.class_list.addItem(QListWidgetItem(folder_name))

        if self.class_list.count() > 0:
            self.class_list.setCurrentRow(0)

        self.status.set_success("Index ready.")

    # ---- Occurrences + preview ----
    def _rebuild_occ_list(self) -> None:
        self.occ_list.clear()
        self.preview.set_image(None)

        if not self._index:
            return
        cur = self.class_list.currentItem()
        if not cur:
            return

        folder = cur.text()
        items = self._index.classes.get(folder, [])

        region_choice = self.region_filter.currentText()
        q = (self.search.text() or "").strip().lower()

        for it in items:
            if region_choice != "All" and it.region != region_choice:
                continue
            if q and q not in it.cell_key.lower():
                continue

            # If SourceMap was moved out, it won't exist anymore — skip it.
            if it.source_path and not Path(it.source_path).exists():
                continue

            has_s = "S" if it.source_path else "-"
            has_a = "A" if it.active_path else "-"
            text = f"{it.cell_key} | {it.region} | [{has_s}/{has_a}]"
            li = QListWidgetItem(text)
            li.setData(Qt.ItemDataRole.UserRole, it)
            self.occ_list.addItem(li)

        if self.occ_list.count() > 0:
            self.occ_list.setCurrentRow(0)

    def _get_selected_occurrence(self) -> Optional[OccurrenceItem]:
        cur = self.occ_list.currentItem()
        if not cur:
            return None
        it = cur.data(Qt.ItemDataRole.UserRole)
        return it if isinstance(it, OccurrenceItem) else None

    def _update_preview_for_selected(self) -> None:
        it = self._get_selected_occurrence()
        if not it:
            self.preview.set_image(None)
            return

        which = self.map_filter.currentText()
        if which == "ActiveMap":
            self.preview.set_image(it.active_path)
        else:
            self.preview.set_image(it.source_path)

    # ---- Hotkey labeling (MOVE) ----
    def _hotkey_label(self, label: str) -> None:
        if self._focus_is_typing():
            return

        it = self._get_selected_occurrence()
        if not it:
            return

        out_dir = (self.session.state.out_dir or "").strip()
        if not out_dir:
            return

        human_root = human_root_from_output(Path(out_dir))

        try:
            action = apply_label(it, label=label, human_root=human_root)  # MOVE SourceMap
            self._undo_stack.append(action)

            self.log.append_line(
                f"[LABEL-MOVE] {label} | {it.class_folder} | {it.cell_key} | {it.region} -> {action.dst_path}"
            )
            self.status.set_success(f"Moved to {label}: {it.class_folder}")

            self._consume_current_occurrence_and_advance()
        except Exception as e:
            self.status.set_error("Move failed.")
            QMessageBox.warning(self, "Label failed", str(e))

    def _consume_current_occurrence_and_advance(self) -> None:
        row = self.occ_list.currentRow()
        if row < 0:
            return

        self.occ_list.takeItem(row)

        if row < self.occ_list.count():
            self.occ_list.setCurrentRow(row)
        elif self.occ_list.count() > 0:
            self.occ_list.setCurrentRow(self.occ_list.count() - 1)
        else:
            self.preview.set_image(None)

    # ---- Undo ----
    def _select_occurrence_if_visible(self, *, cell_key: str, region: str) -> bool:
        for i in range(self.occ_list.count()):
            li = self.occ_list.item(i)
            it = li.data(Qt.ItemDataRole.UserRole)
            if isinstance(it, OccurrenceItem) and it.cell_key == cell_key and it.region == region:
                self.occ_list.setCurrentRow(i)
                return True
        return False

    def _select_class_folder(self, folder_name: str) -> None:
        for i in range(self.class_list.count()):
            if self.class_list.item(i).text() == folder_name:
                self.class_list.setCurrentRow(i)
                return

    def _hotkey_undo(self) -> None:
        if not self._undo_stack:
            return

        action = self._undo_stack.pop()
        try:
            undo_label(action)  # move back to original src_path
            self.log.append_line(f"[UNDO] Moved back: {action.src_path}")

            # update UI list to bring it back
            self._select_class_folder(action.class_folder)
            self._rebuild_occ_list()

            ok = self._select_occurrence_if_visible(cell_key=action.cell_key, region=action.region)
            if ok:
                self.status.set_success(f"Restored: {action.class_folder}")
            else:
                self.status.set_info("Restored, but filtered out by current search/region.")
                self.log.append_line("[INFO] Restored occurrence not visible under current filters/search.")
        except Exception as e:
            self.status.set_error("Undo failed.")
            QMessageBox.warning(self, "Undo failed", str(e))
