"""
Fetch pipeline orchestrator.

Responsibilities:
    - Tie together CSV parsing, defect filtering, analysis, and image fetching
      into a single high-level workflow.
    - Yield progress updates for the UI.

This is the main entry point that the UI's fetch tab calls.
"""

from datetime import datetime
from typing import List, Dict, Callable, Optional

from core.csv_parser import read_all_csvs_for_date, discover_csv_files
from core.defect_filter import filter_defect_rows, parse_date, parse_time
from core.defect_analyzer import build_defect_record
from core.image_fetcher import fetch_single_cell
from utils.time_utils import (
    compute_review_range,
    get_dates_for_range,
    time_in_range,
)


def run_fetch(
    end_dt: datetime = None,
    hours: int = 2,
    output_base: str = None,
    on_progress: Callable[[str], None] = None,
    on_cell_complete: Callable[[Dict], None] = None,
) -> Dict:
    """
    Execute the full fetch pipeline.

    Args:
        end_dt: End of review window. Defaults to now.
        hours: Hours to look back.
        output_base: Override output directory.
        on_progress: Callback for progress messages (e.g. for log display).
        on_cell_complete: Callback when a single cell fetch is done.

    Returns:
        Summary dict with keys:
            total_defects, fetched, failed, skipped, results, errors
    """
    def log(msg: str):
        if on_progress:
            on_progress(msg)

    # Step 1: Compute time range
    start_dt, end_dt = compute_review_range(end_dt, hours)
    log(f"Review window: {start_dt.strftime('%Y-%m-%d %H:%M')} to {end_dt.strftime('%Y-%m-%d %H:%M')}")

    # Step 2: Determine which dates to scan
    dates = get_dates_for_range(start_dt, end_dt)
    log(f"Scanning dates: {', '.join(dates)}")

    # Step 3: Read CSVs for each date
    all_rows = []
    for date_str in dates:
        csv_files = discover_csv_files(date_str)
        log(f"  Date {date_str}: found {len(csv_files)} CSV file(s)")
        for fp in csv_files:
            log(f"    - {fp}")
        rows = read_all_csvs_for_date(date_str)
        all_rows.extend(rows)

    log(f"Total rows loaded: {len(all_rows)}")

    # Step 4: Filter to defect rows only
    defect_rows = filter_defect_rows(all_rows)
    log(f"Defect rows (NG/DLNG/C-NG): {len(defect_rows)}")

    # Step 5: Filter by time range
    time_filtered = []
    for row in defect_rows:
        row_date = parse_date(row)
        row_time = parse_time(row)
        if time_in_range(row_time, start_dt, end_dt, row_date):
            time_filtered.append(row)

    log(f"Defects in time window: {len(time_filtered)}")

    # Step 6: Analyze each defect and fetch images
    results = []
    errors = []
    fetched = 0
    failed = 0

    for i, row in enumerate(time_filtered):
        record = build_defect_record(row)
        cell_id = record["cell_id"]
        defect = record["judge_defect"]
        side = record["side"]

        log(f"[{i+1}/{len(time_filtered)}] {cell_id} | {defect} | side={side}")

        try:
            result = fetch_single_cell(record, output_base)
            if result:
                results.append(result)
                fetched += 1
                log(f"  -> Copied {result['image_count']} images to {result['output_dir']}")
                if on_cell_complete:
                    on_cell_complete(result)
            else:
                failed += 1
                error_info = {
                    "cell_id": cell_id,
                    "reason": "Image folder not found or no images matched",
                }
                errors.append(error_info)
                log(f"  -> FAILED: folder/images not found")
        except Exception as e:
            failed += 1
            error_info = {"cell_id": cell_id, "reason": str(e)}
            errors.append(error_info)
            log(f"  -> ERROR: {e}")

    # Summary
    log(f"\nFetch complete: {fetched} succeeded, {failed} failed out of {len(time_filtered)} defects")

    return {
        "total_defects": len(time_filtered),
        "fetched": fetched,
        "failed": failed,
        "results": results,
        "errors": errors,
        "start_dt": start_dt,
        "end_dt": end_dt,
    }