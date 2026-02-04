from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from .pc_registry import PcInfo
from .remote_path_resolver import find_remote_crop_b_roots, RemoteCropBRoot
from .scanner import scan

LogFn = Optional[Callable[[str], None]]
ProgressFn = Optional[Callable[[int, int], None]]  # done,total
CancelFn = Optional[Callable[[], bool]]
DetailProgressFn = Optional[Callable[[int, int, str, str], None]]  # done,total,class,file


@dataclass
class FetchRemoteStats:
    total_copied: int
    total_overwritten: int
    missing_days: int
    missing_pcs: int
    active_included: int
    active_missing: int
    per_class_copied: Dict[str, int]


def _log(fn: LogFn, msg: str) -> None:
    if fn:
        fn(msg)


def _progress(fn: ProgressFn, done: int, total: int) -> None:
    if fn:
        fn(done, total)


def _detail(fn: DetailProgressFn, done: int, total: int, class_name: str, filename: str) -> None:
    if fn:
        fn(done, total, class_name, filename)


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def fetch_images_remote(
    *,
    pcs: List[PcInfo],
    days: List[date],
    out_dir: Path,
    model: str,
    include_activemap: bool,
    log: LogFn = None,
    progress: ProgressFn = None,
    detail_progress: DetailProgressFn = None,
    is_cancelled: CancelFn = None,
) -> FetchRemoteStats:
    """
    Remote-only fetch:
      - For each selected PC, for each day, search E/F/G for Crop_B root (rollover-safe)
      - Scan and merge all files into out_dir/<class_name>/...
      - Overwrite on collisions
      - Skip offline/unreachable PCs and continue
    """

    out_dir = out_dir.expanduser().resolve()
    _ensure_dir(out_dir)

    _log(log, f"[INFO] Remote fetch PCs: {len(pcs)} | days: {len(days)} | model={model} | include_activemap={include_activemap}")

    # Pre-scan to compute total files (keeps progress bar correct)
    scan_jobs: List[Tuple[PcInfo, date, RemoteCropBRoot, object]] = []
    total_files = 0
    missing_days = 0
    missing_pcs = 0
    total_active_included = 0
    total_active_missing = 0

    for pc in pcs:
        if is_cancelled and is_cancelled():
            _log(log, "[WARN] Cancelled during pre-scan.")
            return FetchRemoteStats(0, 0, 0, 0, 0, 0, {})

        any_found_for_pc = False

        for day in days:
            roots = find_remote_crop_b_roots(pc=pc, model=model, day=day)
            if not roots:
                continue

            any_found_for_pc = True
            for r in roots:
                if is_cancelled and is_cancelled():
                    _log(log, "[WARN] Cancelled during pre-scan.")
                    return FetchRemoteStats(0, 0, missing_days, missing_pcs, 0, 0, {})

                _log(log, f"[OK] [{pc.key}] {day} -> {r.drive}: {r.path}")
                try:
                    sr = scan(r.path, include_activemap=include_activemap)
                except Exception as e:
                    _log(log, f"[WARN] [{pc.key}] scan failed: {r.path} ({e})")
                    continue

                scan_jobs.append((pc, day, r, sr))
                total_active_included += sr.included_activemap_count
                total_active_missing += sr.missing_activemap_count
                for _, files in sr.files_by_class.items():
                    total_files += len(files)

        if not any_found_for_pc:
            missing_pcs += 1
            _log(log, f"[WARN] [{pc.key}] No Crop_B folders found for selected day(s). (PC offline or no data)")

    if total_files == 0:
        _log(log, "[WARN] Nothing to copy (0 files).")
        _progress(progress, 0, 0)
        return FetchRemoteStats(0, 0, missing_days, missing_pcs, total_active_included, total_active_missing, {})

    _log(log, f"[INFO] Total files to copy: {total_files}")
    if include_activemap:
        _log(log, f"[INFO] ActiveMap included: {total_active_included} | missing pairs: {total_active_missing}")

    done = 0
    total_copied = 0
    total_overwritten = 0
    per_class_copied: Dict[str, int] = {}

    _progress(progress, 0, total_files)

    for pc, day, root, sr in scan_jobs:
        for class_name, files in sr.files_by_class.items():
            if not files:
                continue

            dest_dir = out_dir / class_name
            _ensure_dir(dest_dir)

            for src in files:
                if is_cancelled and is_cancelled():
                    _log(log, "[WARN] Cancelled during copy.")
                    _progress(progress, done, total_files)
                    return FetchRemoteStats(
                        total_copied, total_overwritten, missing_days, missing_pcs,
                        total_active_included, total_active_missing, per_class_copied
                    )

                dst = dest_dir / src.name
                try:
                    if dst.exists():
                        total_overwritten += 1
                    shutil.copy2(src, dst)
                except Exception as e:
                    _log(log, f"[WARN] copy failed: {src} -> {dst} ({e})")
                    # still advance progress to avoid stalling
                else:
                    total_copied += 1
                    per_class_copied[class_name] = per_class_copied.get(class_name, 0) + 1

                done += 1
                _detail(detail_progress, done, total_files, class_name, src.name)
                _progress(progress, done, total_files)

    _log(log, f"[DONE] Copied {total_copied} files (overwrote {total_overwritten}). Missing PCs: {missing_pcs}")
    return FetchRemoteStats(
        total_copied, total_overwritten, missing_days, missing_pcs,
        total_active_included, total_active_missing, per_class_copied
    )
