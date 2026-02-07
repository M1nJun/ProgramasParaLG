from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from .pc_registry import PcInfo

LogFn = Optional[Callable[[str], None]]
ProgressFn = Optional[Callable[[int, int], None]]  # done, total
CancelFn = Optional[Callable[[], bool]]


@dataclass
class RemoteCsvFetchStats:
    total_found: int = 0
    total_copied: int = 0
    total_overwritten: int = 0
    pcs_with_missing_dir: int = 0
    pcs_with_no_csv: int = 0
    missing_pcs: int = 0


def _log(fn: LogFn, msg: str) -> None:
    if fn:
        fn(msg)


def _progress(fn: ProgressFn, done: int, total: int) -> None:
    if fn:
        fn(done, total)


def _yyyymmdd(d: date) -> str:
    return d.strftime("%Y%m%d")


def _is_ignored_csv(path: Path) -> bool:
    # keep consistent with your existing local autofind logic
    name = path.name.lower()
    return name.endswith("_defect.csv")


def _find_csvs_for_day(csv_dir: Path, model: str, day: date) -> List[Path]:
    """
    Find all CSV files for a day/model in a directory.

    Supports:
      #5-2 WELDING VISION(-)_JF2_20260127.csv
      #5-2 WELDING VISION(-)_JF2_20260127_1.csv
      #5-2 WELDING VISION(+)_JF2_20260127_2.csv
      etc.
    """
    model = (model or "").strip()
    if not model:
        raise ValueError("model is required (e.g., JF2)")

    d = _yyyymmdd(day)

    pat_base = f"#*-* WELDING VISION(*)_{model}_{d}.csv"
    pat_suffix = f"#*-* WELDING VISION(*)_{model}_{d}_*.csv"

    hits = list(csv_dir.glob(pat_base)) + list(csv_dir.glob(pat_suffix))
    uniq = {p for p in hits if p.is_file() and not _is_ignored_csv(p)}

    def sort_key(p: Path):
        name = p.name
        # base file first, then _1, _2... by suffix if present
        n = 0
        stem = name[:-4] if name.lower().endswith(".csv") else name
        if "_" in stem:
            tail = stem.rsplit("_", 1)[-1]
            if tail.isdigit():
                n = int(tail)
        return (n, name.lower())

    return sorted(uniq, key=sort_key)


def _unc_csv_dir(ip: str) -> Path:
    # Your confirmed format:
    # \\IP\D\Files\Data\Result\Day
    return Path(f"\\\\{ip}\\D\\Files\\Data\\Result\\Day")


def fetch_csvs_remote(
    *,
    pcs: List[PcInfo],
    days: List[date],
    out_dir: Path,
    model: str,
    log: LogFn = None,
    progress: ProgressFn = None,
    is_cancelled: CancelFn = None,
) -> Tuple[List[Path], RemoteCsvFetchStats]:
    """
    Fetch CSVs from each PC's:
      \\<ip>\D\Files\Data\Result\Day

    Cache into:
      <out_dir>\_summary_csv_cache\

    Returns (cached_paths, stats).
    """
    out_dir = Path(out_dir).expanduser().resolve()
    cache_dir = out_dir / "_summary_csv_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    pcs = pcs or []
    days = sorted(days or [])
    total_steps = len(pcs) * max(1, len(days))
    done_steps = 0

    stats = RemoteCsvFetchStats()
    cached_paths: List[Path] = []

    _log(log, f"[CSV] Cache dir: {cache_dir}")
    _log(log, f"[CSV] PCs: {len(pcs)} | Days: {len(days)} | Model: {model}")

    for pc in pcs:
        if is_cancelled and is_cancelled():
            _log(log, "[CSV] Cancelled.")
            break

        if not pc.ip:
            stats.missing_pcs += 1
            _log(log, f"[CSV][WARN] Missing IP for PC: {pc.key}")
            continue

        remote_dir = _unc_csv_dir(pc.ip)
        if not remote_dir.exists():
            stats.pcs_with_missing_dir += 1
            _log(log, f"[CSV][WARN] Missing remote dir: {remote_dir} ({pc.key})")
            # still advance progress for each day so progress bar feels right
            for _ in days:
                done_steps += 1
                _progress(progress, done_steps, total_steps)
            continue

        pc_found_any = False

        for d in days:
            if is_cancelled and is_cancelled():
                _log(log, "[CSV] Cancelled.")
                break

            found = _find_csvs_for_day(remote_dir, model=model, day=d)
            stats.total_found += len(found)
            if found:
                pc_found_any = True
                _log(log, f"[CSV] {pc.key} {d}: found {len(found)} file(s)")

            # Copy each found file into cache (flat), prefixing with pc.key to avoid collisions
            for src in found:
                dst = cache_dir / f"{pc.key}__{src.name}"
                if dst.exists():
                    stats.total_overwritten += 1
                try:
                    dst.write_bytes(src.read_bytes())  # reliable across SMB; avoids some metadata issues
                    stats.total_copied += 1
                    cached_paths.append(dst)
                except Exception as e:
                    _log(log, f"[CSV][WARN] Copy failed: {src} -> {dst} ({e})")

            done_steps += 1
            _progress(progress, done_steps, total_steps)

        if not pc_found_any:
            stats.pcs_with_no_csv += 1
            _log(log, f"[CSV][INFO] {pc.key}: no CSV matched for selected days/model.")

    # Deduplicate output list (just in case)
    uniq = []
    seen = set()
    for p in cached_paths:
        rp = str(p.resolve())
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)

    _log(
        log,
        f"[CSV] Done. copied={stats.total_copied}, overwritten={stats.total_overwritten}, "
        f"pcs_missing_dir={stats.pcs_with_missing_dir}, pcs_no_csv={stats.pcs_with_no_csv}"
    )
    return uniq, stats