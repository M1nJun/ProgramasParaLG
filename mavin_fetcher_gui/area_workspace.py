from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QTabWidget, QVBoxLayout

from mavin_fetcher.area_spec import AreaSpec

from .fetch_tab import FetchTab
from .summary_tab import SummaryTab
from .viewer_tab import ViewerTab
from .scroll_wrap import wrap_scroll
from .session_manager import SessionManager
from .settings_store import AreaSettings


class AreaWorkspace(QWidget):
    """
    One "Area" page containing:
      - Fetch tab
      - Summary tab
      - Viewer tab

    This is intentionally reusable for A and B.
    """

    def __init__(self, *, area: AreaSpec, session: SessionManager):
        super().__init__()
        self.area = area
        self.session = session

        self.fetch_tab = FetchTab(self.session, area=self.area)
        self.summary_tab = SummaryTab(self.session, area=self.area)
        self.viewer_tab = ViewerTab(self.session, area=self.area)

        tabs = QTabWidget()
        tabs.addTab(wrap_scroll(self.fetch_tab), "Fetch")
        tabs.addTab(wrap_scroll(self.summary_tab), "Summary")
        tabs.addTab(wrap_scroll(self.viewer_tab), "Viewer")

        root = QVBoxLayout(self)
        root.addWidget(tabs)

        self._tabs = tabs

        # Summary -> Viewer jump (within this Area)
        self.summary_tab.class_selected.connect(self._jump_to_viewer)

    def _jump_to_viewer(self, class_key: str) -> None:
        self._tabs.setCurrentIndex(2)
        self.viewer_tab.show_class_key(class_key)

    def apply_settings(self, s: AreaSettings) -> None:
        self.fetch_tab.apply_settings(s)
        self.summary_tab.apply_settings(s)

    def collect_settings(self) -> AreaSettings:
        # Start from the current session state + per-tab settings
        state = self.session.state

        out = AreaSettings(
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

        fetch_state = self.fetch_tab.collect_settings()
        out.include_activemap = bool(fetch_state.get("include_activemap", out.include_activemap))

        sum_state = self.summary_tab.collect_settings()
        out.summary_csv_paths = sum_state.get("summary_csv_paths", []) or []
        out.summary_top_n = int(sum_state.get("summary_top_n", out.summary_top_n))

        return out