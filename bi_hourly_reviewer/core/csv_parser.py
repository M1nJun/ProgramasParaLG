"""
CSV file discovery and reading.

Responsibilities:
    - Discover CSV files for a given date in the CSV base directory.
    - Filter out defect summary CSVs.
    - Handle split files (_1, _2, etc.).
    - Read CSV rows into a list of dictionaries.

Does NOT filter by time or judge — that is handled by defect_filter.py.
"""

import csv
import os
import re
from typing import List, Dict, Any

from config import CSV_BASE_DIR, CSV_DEFECT_SUFFIX


def discover_csv_files(date_str: str, base_dir: str = None) -> List[str]:
    """
    Find all relevant CSV files for a given date.

    Args:
        date_str: Date in YYYYMMDD format (e.g. "20260305").
        base_dir: Override CSV directory. Defaults to CSV_BASE_DIR.

    Returns:
        List of full file paths to matching CSVs.
    """
    base = base_dir or CSV_BASE_DIR
    if not os.path.isdir(base):
        return []

    matched = []
    for fname in os.listdir(base):
        if not fname.lower().endswith(".csv"):
            continue
        if _is_defect_csv(fname):
            continue
        if _matches_date(fname, date_str):
            matched.append(os.path.join(base, fname))

    return sorted(matched)


def _is_defect_csv(filename: str) -> bool:
    """
    Check if a filename is a defect summary CSV (to be ignored).

    Example ignored: #3-1 WELDING VISION(-)_JF2_20260306_defect.csv
    """
    name_no_ext = os.path.splitext(filename)[0]
    return name_no_ext.lower().endswith(CSV_DEFECT_SUFFIX.lower())


def _matches_date(filename: str, date_str: str) -> bool:
    """
    Check if a CSV filename contains the given date string.

    Matches:
        #3-1 WELDING VISION(-)_JF2_20260305.csv
        #3-1 WELDING VISION(-)_JF2_20260305_1.csv
        #3-1 WELDING VISION(-)_JF2_20260305_2.csv

    Does NOT match:
        #3-1 WELDING VISION(-)_JF2_20260305_defect.csv  (already filtered)
        #3-1 WELDING VISION(-)_JF2_20260306.csv          (wrong date)
    """
    name_no_ext = os.path.splitext(filename)[0]
    # After removing _defect (already filtered), check if date_str appears
    # Pattern: ..._{date_str}.csv or ..._{date_str}_{number}.csv
    pattern = rf"_{date_str}(?:_(\d+))?$"
    return bool(re.search(pattern, name_no_ext))


def read_csv_file(filepath: str) -> List[Dict[str, str]]:
    """
    Read a single CSV file and return rows as list of dicts.

    Args:
        filepath: Full path to the CSV file.

    Returns:
        List of row dicts keyed by column header.
    """
    rows = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def read_all_csvs_for_date(date_str: str, base_dir: str = None) -> List[Dict[str, str]]:
    """
    Discover and read all CSV files for a given date.
    Combines rows from all matched files (including split files).

    Args:
        date_str: Date in YYYYMMDD format.
        base_dir: Override CSV directory.

    Returns:
        Combined list of row dicts from all matching CSVs.
    """
    filepaths = discover_csv_files(date_str, base_dir)
    all_rows = []
    for fp in filepaths:
        all_rows.extend(read_csv_file(fp))
    return all_rows


def extract_station_name(filepath: str) -> str:
    """
    Extract the station identifier from a CSV filename.

    Example:
        "#3-1 WELDING VISION(-)_JF2_20260305.csv" -> "#3-1 WELDING VISION(-)"

    Useful for display/logging purposes.
    """
    fname = os.path.basename(filepath)
    name_no_ext = os.path.splitext(fname)[0]
    # Station name is everything before the first _<MODEL> segment
    # Pattern: <station>_<model>_<date>...
    # Find the model by looking for the segment before the date
    parts = name_no_ext.split("_")
    # Walk backwards to find the date segment, station is everything before model
    for i, part in enumerate(parts):
        if re.match(r"^\d{8}$", part):
            # Date found at index i, model is at i-1, station is 0..i-2
            if i >= 2:
                station = "_".join(parts[: i - 1])
                return station
            break
    return name_no_ext