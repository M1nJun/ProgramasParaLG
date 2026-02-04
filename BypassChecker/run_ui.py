import sys
from PyQt6.QtWidgets import QApplication
from ui_app import AppTabs

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = AppTabs()
    w.show()
    sys.exit(app.exec())
