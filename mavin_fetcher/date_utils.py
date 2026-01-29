from __future__ import annotations

from datetime import date, timedelta


def parse_ymd(s: str) -> date:
    """
    Accepts:
      - YYYY-MM-DD
      - YYYY/MM/DD
      - YYYY.MM.DD
    """
    s = s.strip().replace("/", "-").replace(".", "-")
    parts = s.split("-")
    if len(parts) != 3:
        raise ValueError(f"Invalid date format: {s!r}. Use YYYY-MM-DD.")
    y, m, d = (int(parts[0]), int(parts[1]), int(parts[2]))
    return date(y, m, d)


def ymd_parts(d: date) -> tuple[str, str, str]:
    return (f"{d.year:04d}", f"{d.month:02d}", f"{d.day:02d}")

def date_range_inclusive(start: date, end: date) -> list[date]:
    if end < start:
        start, end = end, start
    out: list[date] = []
    cur = start
    while cur <= end:
        out.append(cur)
        cur += timedelta(days=1)
    return out


def parse_dates_csv(s: str) -> list[date]:
    """
    Parses a comma-separated list of dates.
    Example: "2026-01-27, 2026-01-28,2026/01/30"
    """
    parts = [x.strip() for x in s.split(",") if x.strip()]
    return [parse_ymd(p) for p in parts]
