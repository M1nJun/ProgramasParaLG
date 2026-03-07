"""
Defect row filtering.

Responsibilities:
    - Filter rows by JUDGE value (NG, DLNG, C-NG).
    - Filter rows by time range.
    - Parse DATE and TIME columns into Python objects.

Does NOT determine defect side — that is handled by defect_analyzer.py.
"""

from datetime import datetime, time, timedelta
from typing import List, Dict, Any, Tuple

from config import COL_DATE, COL_TIME, COL_JUDGE, JUDGE_DEFECT_VALUES


def filter_defect_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Return only rows where JUDGE is a defect value (NG, DLNG, C-NG).
    """
    return [r for r in rows if r.get(COL_JUDGE, "").strip() in JUDGE_DEFECT_VALUES]


def filter_by_time_range(
    rows: List[Dict[str, str]],
    start_time: time,
    end_time: time,
) -> List[Dict[str, str]]:
    """
    Return rows whose TIME falls within [start_time, end_time).

    Args:
        rows: List of row dicts.
        start_time: Inclusive start (datetime.time).
        end_time: Exclusive end (datetime.time).

    Returns:
        Filtered list of rows.
    """
    filtered = []
    for row in rows:
        row_time = parse_time(row)
        if row_time is None:
            continue
        if start_time <= row_time < end_time:
            filtered.append(row)
    return filtered


def parse_date(row: Dict[str, str]) -> str:
    """
    Extract the DATE value from a row as a YYYYMMDD string.
    Handles both integer-like ("20260228") and formatted strings.
    """
    raw = str(row.get(COL_DATE, "")).strip()
    # Remove any decimal if read as float (e.g. "20260228.0")
    if "." in raw:
        raw = raw.split(".")[0]
    return raw


def parse_time(row: Dict[str, str]) -> time:
    """
    Extract the TIME value from a row as a datetime.time object.

    Handles formats:
        "HH:MM:SS"
        "H:MM:SS"
        "HHMMSS"
    """
    raw = str(row.get(COL_TIME, "")).strip()
    if not raw:
        return None

    try:
        if ":" in raw:
            parts = raw.split(":")
            return time(int(parts[0]), int(parts[1]), int(parts[2]))
        elif len(raw) == 6:
            return time(int(raw[0:2]), int(raw[2:4]), int(raw[4:6]))
    except (ValueError, IndexError):
        return None

    return None


def compute_time_range(end_dt: datetime, hours: int) -> Tuple[datetime, datetime]:
    """
    Given an end datetime and a duration in hours, compute start and end.

    Args:
        end_dt: The end of the review window.
        hours: How many hours back to go.

    Returns:
        (start_datetime, end_datetime) tuple.
    """
    start_dt = end_dt - timedelta(hours=hours)
    return start_dt, end_dt


def get_dates_in_range(start_dt: datetime, end_dt: datetime) -> List[str]:
    """
    Return all dates (as YYYYMMDD strings) that fall within the range.
    Needed because a time range can span midnight (two dates).
    """
    dates = set()
    current = start_dt.date()
    end_date = end_dt.date()
    while current <= end_date:
        dates.add(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return sorted(dates)