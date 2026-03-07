"""
Time utility functions.

Responsibilities:
    - Compute review time ranges.
    - Format time values for display.
    - Handle midnight-spanning ranges.
"""

from datetime import datetime, time, timedelta
from typing import Tuple, List


def compute_review_range(
    end_dt: datetime = None,
    hours: int = 2,
) -> Tuple[datetime, datetime]:
    """
    Compute the review time range ending at end_dt going back N hours.

    Args:
        end_dt: End of review window. Defaults to current time.
        hours: Number of hours to look back.

    Returns:
        (start_datetime, end_datetime) tuple.
    """
    if end_dt is None:
        end_dt = datetime.now()
    start_dt = end_dt - timedelta(hours=hours)
    return start_dt, end_dt


def get_dates_for_range(start_dt: datetime, end_dt: datetime) -> List[str]:
    """
    Get all dates (YYYYMMDD) that fall within a datetime range.
    Handles midnight crossings.
    """
    dates = set()
    current = start_dt.date()
    end_date = end_dt.date()
    while current <= end_date:
        dates.add(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return sorted(dates)


def time_in_range(row_time: time, start_dt: datetime, end_dt: datetime, row_date_str: str) -> bool:
    """
    Check if a row's date+time falls within the review range.

    Args:
        row_time: Time from the CSV row.
        start_dt: Start of review window (datetime).
        end_dt: End of review window (datetime).
        row_date_str: Date string from the CSV row (YYYYMMDD).

    Returns:
        True if within range.
    """
    if row_time is None:
        return False

    try:
        row_date = datetime.strptime(row_date_str, "%Y%m%d").date()
    except (ValueError, TypeError):
        return False

    row_dt = datetime.combine(row_date, row_time)
    return start_dt <= row_dt < end_dt


def format_time_display(t: time) -> str:
    """Format a time object for display: HH:MM:SS."""
    if t is None:
        return "--:--:--"
    return t.strftime("%H:%M:%S")


def format_datetime_display(dt: datetime) -> str:
    """Format a datetime for display: YYYY-MM-DD HH:MM:SS."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")