from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QGroupBox, QFormLayout, QHBoxLayout,
    QLineEdit, QPushButton, QVBoxLayout
)

from .file_pickers import pick_folder
from .date_selector import DateSelectorWidget
from .session_manager import SessionManager
from .session_state import SessionState
from .horn_lead_output_defaults import suggest_horn_lead_output_dir
from .pc_selector import PcSelectorWidget

class HornLeadSessionPanel(QWidget):
    """Separate session UI for HORN LEAD so we don’t touch A/B area logic."""

    def __init__(self, session: SessionManager):
        super().__init__()
        self.session = session
        self._updating_ui = False

        box = QGroupBox("Session (HORN LEAD)")
        form = QFormLayout(box)

        self.model_edit = QLineEdit()
        form.addRow("Model:", self.model_edit)

        self.date_selector = DateSelectorWidget()
        form.addRow(self.date_selector)

        self.pc_selector = PcSelectorWidget()
        form.addRow(self.pc_selector)

        out_row = QHBoxLayout()
        self.out_dir = QLineEdit()
        self.browse_out = QPushButton("Browse…")
        out_row.addWidget(self.out_dir)
        out_row.addWidget(self.browse_out)
        form.addRow("Output folder:", out_row)

        csv_row = QHBoxLayout()
        self.csv_dir = QLineEdit()
        self.browse_csv_dir = QPushButton("Browse…")
        csv_row.addWidget(self.csv_dir)
        csv_row.addWidget(self.browse_csv_dir)
        form.addRow("CSV folder:", csv_row)

        root = QVBoxLayout(self)
        root.addWidget(box)

        self.browse_out.clicked.connect(self._pick_out)
        self.browse_csv_dir.clicked.connect(self._pick_csv_dir)
        self.model_edit.editingFinished.connect(self._push_to_session)
        self.out_dir.editingFinished.connect(self._on_out_dir_user_edited)
        self.csv_dir.editingFinished.connect(self._push_to_session)
        self.date_selector.changed.connect(self._on_dates_changed)
        self.pc_selector.changed.connect(self._push_to_session)

        self.session.changed.connect(self.apply_session)

        self.apply_session(self.session.state)
        self._maybe_apply_default_output()

    def _on_dates_changed(self) -> None:
        self._maybe_apply_default_output()
        self._push_to_session()

    def _maybe_apply_default_output(self) -> None:
        if self._updating_ui:
            return

        ds = self.date_selector.export_state()
        tmp = SessionState(
            model=self.model_edit.text().strip() or "JF2",
            out_dir=self.out_dir.text().strip(),
            out_dir_user_set=self.session.state.out_dir_user_set,
            csv_dir=self.csv_dir.text().strip(),
            selected_pcs=list(self.pc_selector.selected_keys()),
            date_mode=ds.get("date_mode", "Single date"),
            single_date=ds.get("single_date", ""),
            range_start=ds.get("range_start", ""),
            range_end=ds.get("range_end", ""),
            specific_dates=ds.get("specific_dates", []) or [],
        )
        days = tmp.to_days()

        if not self.session.state.out_dir_user_set:
            suggested = suggest_horn_lead_output_dir(days=days)
            self.out_dir.setText(str(suggested))

    def _pick_out(self) -> None:
        picked = pick_folder(self, "Select output folder", self.out_dir.text().strip())
        if picked:
            self.out_dir.setText(picked)
            self.session.update(out_dir_user_set=True, out_dir=picked)
            self._push_to_session()

    def _on_out_dir_user_edited(self) -> None:
        if self._updating_ui:
            return
        text = self.out_dir.text().strip()
        if text:
            self.session.update(out_dir_user_set=True)
        self._push_to_session()

    def _pick_csv_dir(self) -> None:
        picked = pick_folder(self, "Select CSV folder", self.csv_dir.text().strip())
        if picked:
            self.csv_dir.setText(picked)
            self._push_to_session()

    def _push_to_session(self) -> None:
        if self._updating_ui:
            return

        ds = self.date_selector.export_state()
        out_user_set = self.session.state.out_dir_user_set

        s = SessionState(
            model=self.model_edit.text().strip() or "JF2",
            out_dir=self.out_dir.text().strip(),
            out_dir_user_set=out_user_set,
            csv_dir=self.csv_dir.text().strip(),
            selected_pcs=list(self.pc_selector.selected_keys()),
            date_mode=ds.get("date_mode", "Single date"),
            single_date=ds.get("single_date", ""),
            range_start=ds.get("range_start", ""),
            range_end=ds.get("range_end", ""),
            specific_dates=ds.get("specific_dates", []) or [],
        )
        self.session.set_state(s)

    def apply_session(self, s: SessionState) -> None:
        self._updating_ui = True
        try:
            self.model_edit.setText(s.model or "JF2")
            self.out_dir.setText(s.out_dir or "")
            self.csv_dir.setText(s.csv_dir or "")

            self.date_selector.import_state({
                "date_mode": s.date_mode,
                "single_date": s.single_date,
                "range_start": s.range_start,
                "range_end": s.range_end,
                "specific_dates": s.specific_dates or [],
            })

            self.pc_selector.set_selected_keys(list(getattr(s, "selected_pcs", []) or []))
        finally:
            self._updating_ui = False