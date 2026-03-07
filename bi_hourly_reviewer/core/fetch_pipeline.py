"""
Fetch pipeline orchestrator.

Responsibilities:
    - Tie together CSV parsing, defect filtering, analysis, and image fetching
      into a single high-level workflow.
    - Pre-build a crop image cache, then fetch main + crop images per cell.
    - Yield progress updates for the UI.

This is the main entry point that the UI's fetch tab calls.
"""

from datetime import datetime
from typing import List, Dict, Callable, Optional

from core.csv_parser import read_all_csvs_for_date, discover_csv_files
from core.defect_filter import filter_defect_rows, parse_date, parse_time
from core.defect_analyzer import build_defect_record
from core.image_fetcher import fetch_single_cell
from core.crop_cache import CropCache
from core.crop_fetcher import fetch_crops_for_cell
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
            total_defects, fetched, failed, results, errors
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

    if not time_filtered:
        log("\nNo defects found in the time window.")
        return {
            "total_defects": 0,
            "fetched": 0,
            "failed": 0,
            "results": [],
            "errors": [],
            "start_dt": start_dt,
            "end_dt": end_dt,
        }

    # Step 6: Build defect records and pre-build crop cache
    records = [build_defect_record(row) for row in time_filtered]
    crop_cache = _build_crop_cache(records, dates, log)

    # Step 7: Fetch images for each defect
    results = []
    errors = []
    fetched = 0
    failed = 0

    for i, record in enumerate(records):
        cell_id = record["cell_id"]
        defect = record["judge_defect"]
        side = record["side"]

        log(f"[{i+1}/{len(records)}] {cell_id} | {defect} | side={side}")

        try:
            # Fetch main cell images
            result = fetch_single_cell(record, output_base)
            if result:
                results.append(result)
                fetched += 1
                if result['image_count'] > 0:
                    log(f"  -> Copied {result['image_count']} main images")
                else:
                    log(f"  -> Skipped main images ({record['judge']})")

                # Fetch DL crop images using cached index
                crop_result = fetch_crops_for_cell(
                    record, result["output_dir"], crop_cache
                )
                result["crop_result"] = crop_result

                if crop_result["crop_files_copied"] > 0:
                    log(f"  -> Crop images: {crop_result['crop_files_copied']} files")
                for err in crop_result["crop_errors"]:
                    log(f"  -> Crop warning: {err}")

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
    log(f"\nFetch complete: {fetched} succeeded, {failed} failed out of {len(records)} defects")

    return {
        "total_defects": len(records),
        "fetched": fetched,
        "failed": failed,
        "results": results,
        "errors": errors,
        "start_dt": start_dt,
        "end_dt": end_dt,
    }


def _build_crop_cache(
    records: List[Dict],
    dates: List[str],
    log: Callable,
) -> CropCache:
    """
    Pre-build the crop image cache for all defect types in this batch.

    Collects the unique defect types and model IDs, then indexes
    only the crop folders we actually need — once per folder total.
    """
    # Collect unique defect types that have crop configs
    defect_types = set()
    for record in records:
        defect_types.add(record["judge_defect"])

    # Collect unique model IDs (usually just one, but be safe)
    model_ids = set()
    for record in records:
        model_ids.add(record["model_id"])

    # Build cache: index once per (model, date, crop_folder)
    cache = CropCache()
    for model_id in model_ids:
        for date_str in dates:
            cache.build_index(
                model_id=model_id,
                date_str=date_str,
                defect_types=defect_types,
                on_progress=log,
            )

    return cache