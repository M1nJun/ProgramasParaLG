from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .area_spec import AreaSpec, AREA_B
from .config import excluded_class_folders_for_area
from .filename_parser import parse_image_filename
from .pc_registry import PcInfo
from .remote_path_resolver import find_remote_crop_roots, RemoteCropRoot
from .scanner import scan

LogFn = Optional[Callable[[str], None]]
ProgressFn = Optional[Callable[[int, int], None]]
CancelFn = Optional[Callable[[], bool]]
DetailProgressFn = Optional[Callable[[int, int, str, str], None]]


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


def _polarity_from_filename(path: Path) -> Optional[str]:
    parsed = parse_image_filename(path)
    if not parsed:
        return None
    return parsed.polarity  # "ANODE" or "CATHODE"


def fetch_images_remote(
    *,
    pcs: List[PcInfo],
    days: List[date],
    out_dir: Path,
    model: str,
    include_activemap: bool,
    area: AreaSpec = AREA_B,
    log: LogFn = None,
    progress: ProgressFn = None,
    detail_progress: DetailProgressFn = None,
    is_cancelled: CancelFn = None,
) -> FetchRemoteStats:
    """
    Output structure (NEW):
      out_dir\\ANODE\\<class>\\...
      out_dir\\CATHODE\\<class>\\...

    NOTE:
      out_dir is already area-separated by GUI defaults:
        A: D:\\A_AREA_DL_REVIEW\\YYYYMMDD
        B: D:\\B_AREA_DL_REVIEW\\YYYYMMDD
      so we do NOT create extra \\A or \\B under out_dir.
    """
    out_dir = out_dir.expanduser().resolve()
    _ensure_dir(out_dir)

    excluded = excluded_class_folders_for_area(area.area_id)
    _log(log, f"[INFO] Excluding class folders for {area.area_id}: {sorted(excluded)}")
    _log(
        log,
        f"[INFO] Remote fetch ({area.display_name}) PCs: {len(pcs)} | days: {len(days)} | "
        f"model={model} | include_activemap={include_activemap}",
    )

    scan_jobs: List[Tuple[PcInfo, date, RemoteCropRoot, object]] = []
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
            roots = find_remote_crop_roots(pc=pc, model=model, day=day, area=area)
            if not roots:
                continue

            any_found_for_pc = True
            for r in roots:
                if is_cancelled and is_cancelled():
                    _log(log, "[WARN] Cancelled during pre-scan.")
                    return FetchRemoteStats(0, 0, missing_days, missing_pcs, 0, 0, {})

                _log(log, f"[OK] [{pc.key}] {day} -> {r.drive}: {r.path}")
                try:
                    sr = scan(r.path, include_activemap=include_activemap, excluded_class_folders=excluded)
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
            _log(log, f"[WARN] [{pc.key}] No {area.crop_dirname} folders found for selected day(s).")

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

            for src in files:
                if is_cancelled and is_cancelled():
                    _log(log, "[WARN] Cancelled during copy.")
                    _progress(progress, done, total_files)
                    return FetchRemoteStats(
                        total_copied,
                        total_overwritten,
                        missing_days,
                        missing_pcs,
                        total_active_included,
                        total_active_missing,
                        per_class_copied,
                    )

                polarity = _polarity_from_filename(src)
                if polarity not in ("ANODE", "CATHODE"):
                    _log(log, f"[WARN] Cannot detect polarity from filename, skipping: {src.name}")
                    done += 1
                    _detail(detail_progress, done, total_files, class_name, src.name)
                    _progress(progress, done, total_files)
                    continue

                dest_dir = out_dir / polarity / class_name
                _ensure_dir(dest_dir)

                dst = dest_dir / src.name
                try:
                    if dst.exists():
                        total_overwritten += 1
                    shutil.copy2(src, dst)
                except Exception as e:
                    _log(log, f"[WARN] copy failed: {src} -> {dst} ({e})")
                else:
                    total_copied += 1
                    # keep per-class stats separate by polarity to avoid confusion
                    key = f"{polarity}/{class_name}"
                    per_class_copied[key] = per_class_copied.get(key, 0) + 1

                done += 1
                _detail(detail_progress, done, total_files, class_name, src.name)
                _progress(progress, done, total_files)

    _log(
        log,
        f"[DONE] ({area.display_name}) Copied {total_copied} files (overwrote {total_overwritten}). "
        f"Missing PCs: {missing_pcs}",
    )
    return FetchRemoteStats(
        total_copied,
        total_overwritten,
        missing_days,
        missing_pcs,
        total_active_included,
        total_active_missing,
        per_class_copied,
    )