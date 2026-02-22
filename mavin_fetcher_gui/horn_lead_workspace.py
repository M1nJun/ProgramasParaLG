from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QTabWidget, QVBoxLayout

from .horn_lead_fetch_tab import HornLeadFetchTab
from .scroll_wrap import wrap_scroll
from .session_manager import SessionManager
from .settings_store import AreaSettings

class HornLeadWorkspace(QWidget):
    """Top-level tab for HORN LEAD (Fetch only for now)."""

    def __init__(self, *, session: SessionManager):
        super().__init__()
        self.session = session

        self.fetch_tab = HornLeadFetchTab(self.session)

        tabs = QTabWidget()
        tabs.addTab(wrap_scroll(self.fetch_tab), "Fetch")

        root = QVBoxLayout(self)
        root.addWidget(tabs)
        self._tabs = tabs

    def apply_settings(self, s: AreaSettings) -> None:
        # No per-tab settings yet.
        return

    def collect_settings(self) -> AreaSettings:
        state = self.session.state
        return AreaSettings(
            model=state.model,
            out_dir=state.out_dir,
            csv_dir=state.csv_dir,
            selected_pcs=list(getattr(state, "selected_pcs", []) or []),
            date_mode=state.date_mode,
            single_date=state.single_date,
            range_start=state.range_start,
            range_end=state.range_end,
            specific_dates=state.specific_dates or [],
        )