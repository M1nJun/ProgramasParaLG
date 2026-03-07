"""
Central configuration for the Bi-Hourly Image Reviewer.
All paths, constants, and configurable values live here.
"""

import os
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

# JUDGE values that should NOT fetch main cell images (only crop images)
SKIP_MAIN_IMAGES_FOR_JUDGE = {"DLNG", "C-NG"}

# Drives to scan for images (auto-detected at runtime, but can be overridden)
# If empty, all available drives will be scanned
IMAGE_DRIVES_OVERRIDE = []

# =============================================================================
# IMAGE FILE SELECTION
# =============================================================================
# Default: fetch only the _X_2 pair per side (2 images).
# Extended: fetch both _X_0 and _X_2 pairs per side (4 images).

UPPER_IMAGE_PATTERNS_DEFAULT = [
    "_0_2.jpg",
    "_0_2_overlay.jpg",
]

LOWER_IMAGE_PATTERNS_DEFAULT = [
    "_1_2.jpg",
    "_1_2_overlay.jpg",
]

UPPER_IMAGE_PATTERNS_EXTENDED = [
    "_0_0.jpg",
    "_0_0_overlay.jpg",
    "_0_2.jpg",
    "_0_2_overlay.jpg",
]

LOWER_IMAGE_PATTERNS_EXTENDED = [
    "_1_0.jpg",
    "_1_0_overlay.jpg",
    "_1_2.jpg",
    "_1_2_overlay.jpg",
]

# JUDGE-DEFECT values that require the extended (4-image) set
EXTENDED_IMAGE_DEFECTS = {
    "G_TLL", "G_TLR", "G_TFL1", "G_TFR1", "G_TFL2", "G_TFR2",
    "TL", "Hole_Cnt",
    "LONG_TAPE_L", "LONG_TAPE_R",
    "LONG_TAPE_L1", "LONG_TAPE_R1",
    "LONG_TAPE_L2", "LONG_TAPE_R2",
    "LONG_TAPE_L3", "LONG_TAPE_R3",
    "LONG_TAPE_L4", "LONG_TAPE_R4",
}

# =============================================================================
# SIDE DETECTION
# =============================================================================
# Two naming conventions for side-specific columns:
# Case 1 (OK/NG): LOWER_<defect>-OK/NG, UPPER_<defect>-OK/NG
# Case 2 (JUDGE): LOWER_<defect>-JUDGE, UPPER_<defect>-JUDGE
SIDE_COLUMN_SUFFIXES = ["-OK/NG", "-JUDGE"]

# =============================================================================
# DL CROP IMAGES
# =============================================================================
# Mavin crop folder lives at the day level (no hour subfolder):
#   <Drive>:\Files\Image\<MODEL>\<YYYY>\<MM>\<DD>\Mavin\<crop_folder>\...
MAVIN_FOLDER = "Mavin"

# Mapping from JUDGE-DEFECT values to their crop configurations.
#
# Each entry defines:
#   "crop_folder"    : subfolder under Mavin (e.g. "Crop_A", "Gap_DL")
#   "has_subfolders" : whether images are inside class subfolders (True)
#                      or directly in the crop folder (False)
#   "match_tokens"   : list of filename tokens to search for, combined with
#                      cell_id and side. These are the defect position identifiers
#                      in the crop image filenames.
#   "side_override"  : if set, forces a specific side regardless of CSV detection
#                      (e.g. HORNMARK/LEADEDGE are always UPPER)
#
# To add a new defect type, just add an entry here.

CROP_DEFECT_MAP = {
    # A model crops
    "A_L": {
        "crop_folder": "Crop_A",
        "has_subfolders": True,
        "match_tokens": ["A_L"],
    },
    "A_R": {
        "crop_folder": "Crop_A",
        "has_subfolders": True,
        "match_tokens": ["A_R"],
    },

    # B model crops
    "B_L": {
        "crop_folder": "Crop_B",
        "has_subfolders": True,
        "match_tokens": ["B_L"],
    },
    "B_R": {
        "crop_folder": "Crop_B",
        "has_subfolders": True,
        "match_tokens": ["B_R"],
    },

    # Gap DL crops
    "GAP_DL": {
        "crop_folder": "Gap_DL",
        "has_subfolders": False,
        "match_tokens": ["Gap_DL"],
    },

    # B_DIM triggers both HORNMARK and LEADEDGE (always UPPER)
    "B_DIM_L": [
        {
            "crop_folder": "HORNMARK",
            "has_subfolders": False,
            "match_tokens": ["HORNMARK_L"],
            "side_override": "UPPER",
        },
        {
            "crop_folder": "LEADEDGE",
            "has_subfolders": False,
            "match_tokens": ["LEAD EDGE L"],
            "side_override": "UPPER",
        },
    ],
    "B_DIM_R": [
        {
            "crop_folder": "HORNMARK",
            "has_subfolders": False,
            "match_tokens": ["HORNMARK_R"],
            "side_override": "UPPER",
        },
        {
            "crop_folder": "LEADEDGE",
            "has_subfolders": False,
            "match_tokens": ["LEAD EDGE R"],
            "side_override": "UPPER",
        },
    ],

    # C_DIM triggers both SEGMENTATION (bead) and LEADEDGE (always UPPER)
    "C_DIM_L": [
        {
            "crop_folder": "SEGMENTATION",
            "has_subfolders": False,
            "match_tokens": ["TOP BEAD"],
            "side_override": "UPPER",
        },
        {
            "crop_folder": "LEADEDGE",
            "has_subfolders": False,
            "match_tokens": ["LEAD EDGE L"],
            "side_override": "UPPER",
        },
    ],
    "C_DIM_R": [
        {
            "crop_folder": "SEGMENTATION",
            "has_subfolders": False,
            "match_tokens": ["TOP BEAD"],
            "side_override": "UPPER",
        },
        {
            "crop_folder": "LEADEDGE",
            "has_subfolders": False,
            "match_tokens": ["LEAD EDGE R"],
            "side_override": "UPPER",
        },
    ],

    # H_DIM triggers HORNMARK (always UPPER)
    "H_DIM_L": {
        "crop_folder": "HORNMARK",
        "has_subfolders": False,
        "match_tokens": ["HORNMARK_L"],
        "side_override": "UPPER",
    },
    "H_DIM_R": {
        "crop_folder": "HORNMARK",
        "has_subfolders": False,
        "match_tokens": ["HORNMARK_R"],
        "side_override": "UPPER",
    },

    # SEPA DL crops
    "SEPA_DL": {
        "crop_folder": "SEPA",
        "has_subfolders": False,
        "match_tokens": ["SEPA DL"],
    },

    # Bead segmentation crops (different token per side)
    "BEAD_CNT": [
        {
            "crop_folder": "SEGMENTATION",
            "has_subfolders": False,
            "match_tokens": ["TOP BEAD"],
            "side_override": "UPPER",
        },
        {
            "crop_folder": "SEGMENTATION",
            "has_subfolders": False,
            "match_tokens": ["BTM_BEAD"],
            "side_override": "LOWER",
        },
    ],

    # BURNT crops
    "BURNT": {
        "crop_folder": "BURNT",
        "has_subfolders": False,
        "match_tokens": ["BURNT"],
    },

    # Micro model crops (class subfolders)
    "Micro_LL": {
        "crop_folder": "Crop_micro",
        "has_subfolders": True,
        "match_tokens": ["Micro_LL"],
    },
    "Micro_LM": {
        "crop_folder": "Crop_micro",
        "has_subfolders": True,
        "match_tokens": ["Micro_LM"],
    },
    "Micro_MM": {
        "crop_folder": "Crop_micro",
        "has_subfolders": True,
        "match_tokens": ["Micro_MM"],
    },
    "Micro_MR": {
        "crop_folder": "Crop_micro",
        "has_subfolders": True,
        "match_tokens": ["Micro_MR"],
    },
    "Micro_RR": {
        "crop_folder": "Crop_micro",
        "has_subfolders": True,
        "match_tokens": ["Micro_RR"],
    },
}

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
        drive_path = f"{letter}:\\"
        if os.path.exists(drive_path):
            drives.append(letter)
    return drives