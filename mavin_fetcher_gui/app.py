from __future__ import annotations

import sys
from PyQt6.QtWidgets import QApplication

# Works in both cases:
# 1) python -m mavin_fetcher_gui.app   (package context)
# 2) PyInstaller running app.py as a script (no parent package)
try:
    from .main_window import MainWindow  # type: ignore
except ImportError:
    from mavin_fetcher_gui.main_window import MainWindow  # type: ignore


def main() -> int:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
