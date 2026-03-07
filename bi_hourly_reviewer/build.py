"""
Build script for packaging Bi-Hourly Image Reviewer as a standalone .exe.

Prerequisites:
    pip install pyinstaller

Usage:
    python build.py

Output:
    dist/BiHourlyReviewer/BiHourlyReviewer.exe  (one-folder mode, recommended)

    For a single .exe file instead (slower startup):
    python build.py --onefile
"""

import subprocess
import sys
import os


def build(onefile: bool = False):
    """Run PyInstaller to package the application."""

    # Ensure we're in the project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "BiHourlyReviewer",
        "--windowed",                  # No console window
        "--noconfirm",                 # Overwrite without asking
        "--clean",                     # Clean cache before building

        # Explicitly include our packages so PyInstaller finds them
        "--hidden-import", "core",
        "--hidden-import", "core.csv_parser",
        "--hidden-import", "core.defect_filter",
        "--hidden-import", "core.defect_analyzer",
        "--hidden-import", "core.image_locator",
        "--hidden-import", "core.image_selector",
        "--hidden-import", "core.image_fetcher",
        "--hidden-import", "core.fetch_pipeline",
        "--hidden-import", "core.crop_locator",
        "--hidden-import", "core.crop_selector",
        "--hidden-import", "core.crop_fetcher",
        "--hidden-import", "core.crop_cache",
        "--hidden-import", "ui",
        "--hidden-import", "ui.main_window",
        "--hidden-import", "ui.fetch_tab",
        "--hidden-import", "ui.review_tab",
        "--hidden-import", "ui.styles",
        "--hidden-import", "ui.widgets",
        "--hidden-import", "ui.widgets.cell_list",
        "--hidden-import", "ui.widgets.image_viewer",
        "--hidden-import", "utils",
        "--hidden-import", "utils.time_utils",
        "--hidden-import", "utils.file_utils",
        "--hidden-import", "config",

        # Add project root to search paths
        "--paths", project_root,
    ]

    if onefile:
        cmd.append("--onefile")

    # Entry point
    cmd.append("main.py")

    print("Running PyInstaller...")
    print(f"  Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd)

    if result.returncode == 0:
        if onefile:
            exe_path = os.path.join("dist", "BiHourlyReviewer.exe")
        else:
            exe_path = os.path.join("dist", "BiHourlyReviewer", "BiHourlyReviewer.exe")
        print()
        print(f"Build successful!")
        print(f"  Executable: {os.path.abspath(exe_path)}")
    else:
        print()
        print("Build FAILED. Check the output above for errors.")
        sys.exit(1)


if __name__ == "__main__":
    onefile = "--onefile" in sys.argv
    build(onefile=onefile)