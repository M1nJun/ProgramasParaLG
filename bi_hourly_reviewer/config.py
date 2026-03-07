"""
Central configuration for the Bi-Hourly Image Reviewer.
All paths, constants, and configurable values live here.
"""

import string

# =============================================================================
# CSV SOURCE
# =============================================================================
CSV_BASE_DIR = r"D:\Files\Data\Result\Day"

# CSV filename pattern components
# Example: #3-1 WELDING VISION(-)_JF2_20260305.csv
# Example: #5-1 WELDING VISION(+)_JF2_20260306.csv
# Split files: #3-1 WELDING VISION(-)_JF2_20260305_1.csv
# Defect files to ignore: #3-1 WELDING VISION(-)_JF2_20260306_defect.csv
CSV_DEFECT_SUFFIX = "_defect"

# =============================================================================
# JUDGE FILTERING
# =============================================================================
# JUDGE column values we care about
JUDGE_DEFECT_VALUES = {"NG", "DLNG", "C-NG"}

# Values in the side-specific -OK/NG or -JUDGE columns that indicate a defect
SIDE_NG_VALUES = {"NG", "BYPASS_NG"}

# =============================================================================
# IMAGE DIRECTORIES
# =============================================================================
# Image path structure: <Drive>:\Files\Image\<MODEL>\<YYYY>\<MM>\<DD>\<HH>\...
IMAGE_BASE_SUBPATH = r"Files\Image"

# Where NG images go vs DLNG/C-NG images
IMAGE_JUDGE_SUBDIRS = {
    "NG": "NG",
    "DLNG": r"OK\DL_CANDIDATE",
    "C-NG": r"OK\DL_CANDIDATE",
}

# Drives to scan for images (auto-detected at runtime, but can be overridden)
# If empty, all available drives will be scanned
IMAGE_DRIVES_OVERRIDE = []

# =============================================================================
# IMAGE FILE SELECTION
# =============================================================================
# Ending patterns for images to fetch per side.
# Upper side = 0_x patterns, Lower side = 1_x patterns.
UPPER_IMAGE_PATTERNS = [
    "_0_0.jpg",
    "_0_0_overlay.jpg",
    "_0_2.jpg",
    "_0_2_overlay.jpg",
]

LOWER_IMAGE_PATTERNS = [
    "_1_0.jpg",
    "_1_0_overlay.jpg",
    "_1_2.jpg",
    "_1_2_overlay.jpg",
]

# =============================================================================
# SIDE DETECTION
# =============================================================================
# Two naming conventions for side-specific columns:
# Case 1 (OK/NG): LOWER_<defect>-OK/NG, UPPER_<defect>-OK/NG
# Case 2 (JUDGE): LOWER_<defect>-JUDGE, UPPER_<defect>-JUDGE
SIDE_COLUMN_SUFFIXES = ["-OK/NG", "-JUDGE"]

# =============================================================================
# OUTPUT
# =============================================================================
OUTPUT_BASE_DIR = r"D:\BI-HOURLY_REVIEW"
# Output structure: <OUTPUT_BASE_DIR>\<YYYY>\<MM>\<DD>\<HH>\<CELLID> - <JUDGE-DEFECT>\

# =============================================================================
# TIME FRAME
# =============================================================================
DEFAULT_REVIEW_HOURS = 2

# =============================================================================
# CSV COLUMN NAMES
# =============================================================================
COL_NO = "NO"
COL_DATE = "DATE"
COL_TIME = "TIME"
COL_MODEL_ID = "MODEL-ID"
COL_LOT_ID = "LOT-ID"
COL_CELL_ID = "CELL-ID"
COL_JUDGE = "JUDGE"
COL_JUDGE_DEFECT = "JUDGE-DEFECT"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_available_drives():
    """
    Return a list of available drive letters on the system.
    If IMAGE_DRIVES_OVERRIDE is set, use that instead.
    """
    if IMAGE_DRIVES_OVERRIDE:
        return IMAGE_DRIVES_OVERRIDE

    drives = []
    for letter in string.ascii_uppercase:
        import os
        drive_path = f"{letter}:\\"
        if os.path.exists(drive_path):
            drives.append(letter)
    return drives