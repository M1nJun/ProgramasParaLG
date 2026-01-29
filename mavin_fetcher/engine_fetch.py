from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from .path_resolver import find_crop_b_root
from .scanner import scan

LogFn = Optional[Callable[[str], None]]
ProgressFn = Optional[Callable[[int, int], None]]  # (done, total)
CancelFn = Optional[Callable[[], bool]]
DetailProgressFn = Optional[Callable[[int, int, str, str], None]]  # (done, total, class_name, filename)


@dataclass
class FetchStats:
    total_copied: int
    total_overwritten: int
    missing_days: int
    active_included: int
    active_missing: int
    per_class_copied: Dict[str, int]


def _log(fn: LogFn, msg: str) -> None:
    if fn:
        fn(msg)


def _progress(fn: ProgressFn, done: int, total: int) -> None:
    if fn:
        fn(done, total)


def _detail_progress(fn: DetailProgressFn, done: int, total: int, class_name: str, filename: str) -> None:
    # IMPORTANT: call fn with 4 args (done,total,class,filename)
    if fn:
        fn(done, total, class_name, filename)


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def fetch_images(
    *,
    days: List[date],
    out_dir: Path,
    model: str,
    drives: Iterable[str],
    include_activemap: bool,
    log: LogFn = None,
    progress: ProgressFn = None,
    detail_progress: DetailProgressFn = None,
    is_cancelled: CancelFn = None,
) -> FetchStats:
    """
    Core engine for fetching images.
    - Merges all selected days into out_dir/<class_name>/...
    - Overwrites existing file if it already exists.
    - Uses scan() which already excludes 01_OK_* folders.
    """

    out_dir = out_dir.expanduser().resolve()
    _ensure_dir(out_dir)

    # 1) Pre-scan all days to compute total file count and avoid rescanning later
    scanned: List[Tuple[date, Path, object]] = []  # (day, crop_b_root, scan_result)
    missing_days = 0
    total_files = 0
    total_active_included = 0
    total_active_missing = 0

    _log(log, f"[INFO] Fetch days: {len(days)} | model={model} | include_activemap={include_activemap}")

    for day in days:
        if is_cancelled and is_cancelled():
            _log(log, "[WARN] Cancelled during pre-scan.")
            return FetchStats(0, 0, missing_days, 0, 0, {})

        found = find_crop_b_root(model=model, day=day, drives=drives)
        if not found:
            _log(log, f"[WARN] Missing Crop_B folder for {day} (model={model})")
            missing_days += 1
            continue

        _log(log, f"[OK] {day} -> {found.drive}: {found.path}")

        sr = scan(found.path, include_activemap=include_activemap)
        scanned.append((day, found.path, sr))
        total_active_included += sr.included_activemap_count
        total_active_missing += sr.missing_activemap_count

        for _, files in sr.files_by_class.items():
            total_files += len(files)

    if total_files == 0:
        _log(log, "[WARN] Nothing to copy (0 files).")
        _progress(progress, 0, 0)
        return FetchStats(0, 0, missing_days, total_active_included, total_active_missing, {})

    _log(log, f"[INFO] Total files to copy: {total_files}")
    if include_activemap:
        _log(log, f"[INFO] ActiveMap included: {total_active_included} | missing pairs: {total_active_missing}")

    # 2) Copy loop with per-file progress
    done = 0
    total_copied = 0
    total_overwritten = 0
    per_class_copied: Dict[str, int] = {}

    _progress(progress, 0, total_files)

    for _, _, sr in scanned:
        for class_name, files in sr.files_by_class.items():
            if not files:
                continue

            dest_dir = out_dir / class_name
            _ensure_dir(dest_dir)

            for src in files:
                if is_cancelled and is_cancelled():
                    _log(log, "[WARN] Cancelled during copy.")
                    _progress(progress, done, total_files)
                    return FetchStats(
                        total_copied,
                        total_overwritten,
                        missing_days,
                        total_active_included,
                        total_active_missing,
                        per_class_copied,
                    )

                dst = dest_dir / src.name
                if dst.exists():
                    total_overwritten += 1

                shutil.copy2(src, dst)
                total_copied += 1
                per_class_copied[class_name] = per_class_copied.get(class_name, 0) + 1

                done += 1
                _detail_progress(detail_progress, done, total_files, class_name, src.name)
                _progress(progress, done, total_files)

    _log(log, f"[DONE] Copied {total_copied} files (overwrote {total_overwritten}). Missing days: {missing_days}")
    return FetchStats(
        total_copied,
        total_overwritten,
        missing_days,
        total_active_included,
        total_active_missing,
        per_class_copied,
    )
