from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QGroupBox, QFormLayout, QHBoxLayout,
    QLineEdit, QPushButton
)

from .file_pickers import pick_folder
from .date_selector import DateSelectorWidget
from .session_manager import SessionManager
from .session_state import SessionState


class SessionPanel(QWidget):
    """
    Shared session UI:
      - Date selection
      - Model
      - Output folder
      - CSV dir
    Auto-syncs into SessionManager.
    """

    def __init__(self, session: SessionManager):
        super().__init__()
        self.session = session
        self._updating_ui = False

        box = QGroupBox("Session (shared)")
        form = QFormLayout(box)

        self.model_edit = QLineEdit()
        form.addRow("Model:", self.model_edit)

        self.date_selector = DateSelectorWidget()
        form.addRow(self.date_selector)

        # Output folder
        out_row = QHBoxLayout()
        self.out_dir = QLineEdit()
        self.browse_out = QPushButton("Browse…")
        out_row.addWidget(self.out_dir)
        out_row.addWidget(self.browse_out)
        form.addRow("Output folder:", out_row)

        # CSV directory
        csv_row = QHBoxLayout()
        self.csv_dir = QLineEdit()
        self.browse_csv_dir = QPushButton("Browse…")
        csv_row.addWidget(self.csv_dir)
        csv_row.addWidget(self.browse_csv_dir)
        form.addRow("CSV folder:", csv_row)

        # root layout
        from PyQt6.QtWidgets import QVBoxLayout
        root = QVBoxLayout(self)
        root.addWidget(box)

        # ---- wiring ----
        self.browse_out.clicked.connect(self._pick_out)
        self.browse_csv_dir.clicked.connect(self._pick_csv_dir)

        self.model_edit.editingFinished.connect(self._push_to_session)
        self.out_dir.editingFinished.connect(self._push_to_session)
        self.csv_dir.editingFinished.connect(self._push_to_session)

        # NEW: date selector emits changed
        self.date_selector.changed.connect(self._push_to_session)

        # listen to session changes (so both tabs stay in sync)
        self.session.changed.connect(self.apply_session)

        # initial apply
        self.apply_session(self.session.state)

    def _pick_out(self) -> None:
        picked = pick_folder(self, "Select output folder", self.out_dir.text().strip())
        if picked:
            self.out_dir.setText(picked)
            self._push_to_session()

    def _pick_csv_dir(self) -> None:
        picked = pick_folder(self, "Select CSV folder", self.csv_dir.text().strip())
        if picked:
            self.csv_dir.setText(picked)
            self._push_to_session()

    def _push_to_session(self) -> None:
        if self._updating_ui:
            return

        # date state from DateSelectorWidget’s export_state()
        ds = self.date_selector.export_state()

        s = SessionState(
            model=self.model_edit.text().strip() or "JF2",
            out_dir=self.out_dir.text().strip(),
            csv_dir=self.csv_dir.text().strip(),
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
        finally:
            self._updating_ui = False
