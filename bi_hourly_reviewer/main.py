"""
Bi-Hourly Image Reviewer — Application entry point.

Usage:
    python main.py
"""

import sys
import os
import traceback

# Ensure the project root is on the Python path
# so imports like 'from config import ...' work correctly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    try:
        from ui.main_window import launch_app
        launch_app()
    except Exception as e:
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()