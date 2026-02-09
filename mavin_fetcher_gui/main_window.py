from __future__ import annotations

from PyQt6.QtCore import QByteArray
from PyQt6.QtWidgets import QMainWindow, QTabWidget

from mavin_fetcher.area_spec import AREA_A, AREA_B

from .area_workspace import AreaWorkspace
from .session_manager import SessionManager
from .session_state import SessionState
from .settings_store import load_settings, save_settings, Settings


def _session_state_from_area_settings(a) -> SessionState:
    return SessionState(
        model=a.model or "JF2",
        out_dir=a.out_dir or "",
        csv_dir=getattr(a, "csv_dir", r"D:\Files\Data\Result\Day"),
        selected_pcs=list(getattr(a, "selected_pcs", []) or []),
        date_mode=a.date_mode or "Single date",
        single_date=a.single_date or "",
        range_start=a.range_start or "",
        range_end=a.range_end or "",
        specific_dates=a.specific_dates or [],
    )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mavin Fetcher")

        self._settings = load_settings()

        # Two independent sessions (A and B)
        self.session_a = SessionManager(_session_state_from_area_settings(self._settings.area_a))
        self.session_b = SessionManager(_session_state_from_area_settings(self._settings.area_b))

        # Area workspaces
        self.area_a_ws = AreaWorkspace(area=AREA_A, session=self.session_a)
        self.area_b_ws = AreaWorkspace(area=AREA_B, session=self.session_b)

        # Top-level tabs: A Area / B Area
        tabs = QTabWidget()
        tabs.addTab(self.area_a_ws, "A Area")
        tabs.addTab(self.area_b_ws, "B Area")
        self.setCentralWidget(tabs)
        self._tabs = tabs

        # Restore window geometry
        if self._settings.window_geometry_b64:
            try:
                ba = QByteArray.fromBase64(self._settings.window_geometry_b64.encode("ascii"))
                self.restoreGeometry(ba)
            except Exception:
                self.resize(900, 650)
        else:
            self.resize(900, 650)

        # Apply per-area settings to the workspace tabs (fetch/summary internal controls)
        self.area_a_ws.apply_settings(self._settings.area_a)
        self.area_b_ws.apply_settings(self._settings.area_b)

    def closeEvent(self, event) -> None:
        merged = Settings.from_dict(self._settings.to_dict())

        # Pull settings from A workspace
        a_settings = self.area_a_ws.collect_settings()
        merged.area_a = a_settings

        # Pull settings from B workspace
        b_settings = self.area_b_ws.collect_settings()
        merged.area_b = b_settings

        # window geometry
        try:
            merged.window_geometry_b64 = bytes(self.saveGeometry().toBase64()).decode("ascii")
        except Exception:
            merged.window_geometry_b64 = ""

        save_settings(merged)
        super().closeEvent(event)