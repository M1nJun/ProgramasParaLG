from __future__ import annotations

from PyQt6.QtCore import QByteArray
from PyQt6.QtWidgets import QMainWindow, QTabWidget

from .fetch_tab import FetchTab
from .summary_tab import SummaryTab
from .viewer_tab import ViewerTab
from .settings_store import load_settings, save_settings, Settings
from .session_manager import SessionManager
from .session_state import SessionState


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mavin Fetcher")

        self._settings = load_settings()

        # Build shared session from saved settings
        session_state = SessionState(
            model=self._settings.model or "JF2",
            out_dir=self._settings.out_dir or "",
            csv_dir=getattr(self._settings, "csv_dir", r"D:\Files\Data\Result\Day"),
            date_mode=self._settings.date_mode or "Single date",
            single_date=self._settings.single_date or "",
            range_start=self._settings.range_start or "",
            range_end=self._settings.range_end or "",
            specific_dates=self._settings.specific_dates or [],
        )
        self.session = SessionManager(session_state)

        self.fetch_tab = FetchTab(self.session)
        self.summary_tab = SummaryTab(self.session)
        self.viewer_tab = ViewerTab(self.session)

        tabs = QTabWidget()
        tabs.addTab(self.fetch_tab, "Fetch")
        tabs.addTab(self.summary_tab, "Summary")
        tabs.addTab(self.viewer_tab, "Viewer")
        self.setCentralWidget(tabs)

        # store tabs for switching later
        self._tabs = tabs

        # Connect summary -> viewer jump
        self.summary_tab.class_selected.connect(self._jump_to_viewer)

        # Restore window geometry
        if self._settings.window_geometry_b64:
            try:
                ba = QByteArray.fromBase64(self._settings.window_geometry_b64.encode("ascii"))
                self.restoreGeometry(ba)
            except Exception:
                self.resize(900, 650)
        else:
            self.resize(900, 650)

        # Apply non-session settings to tabs
        self.fetch_tab.apply_settings(self._settings)
        self.summary_tab.apply_settings(self._settings)

    def _jump_to_viewer(self, class_key: str) -> None:
        # Switch to viewer tab and ask it to select the class
        self._tabs.setCurrentWidget(self.viewer_tab)
        self.viewer_tab.show_class_key(class_key)

    def closeEvent(self, event) -> None:
        merged = Settings.from_dict(self._settings.to_dict())

        # session -> settings
        s = self.session.state
        merged.model = s.model
        merged.out_dir = s.out_dir
        merged.csv_dir = s.csv_dir
        merged.date_mode = s.date_mode
        merged.single_date = s.single_date
        merged.range_start = s.range_start
        merged.range_end = s.range_end
        merged.specific_dates = s.specific_dates or []

        # per-tab settings
        fetch_state = self.fetch_tab.collect_settings()
        merged.drives_text = fetch_state.get("drives_text", merged.drives_text)
        merged.include_activemap = bool(fetch_state.get("include_activemap", merged.include_activemap))

        sum_state = self.summary_tab.collect_settings()
        merged.summary_csv_paths = sum_state.get("summary_csv_paths", []) or []
        merged.summary_top_n = int(sum_state.get("summary_top_n", merged.summary_top_n))

        # window geometry
        try:
            merged.window_geometry_b64 = bytes(self.saveGeometry().toBase64()).decode("ascii")
        except Exception:
            merged.window_geometry_b64 = ""

        save_settings(merged)
        super().closeEvent(event)
