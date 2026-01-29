from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .config import DEFAULT_DRIVES, DEFAULT_MODEL
from .copy_engine import copy_overwrite
from .csv_summary import summarize as summarize_csv, format_summary
from .date_utils import parse_ymd, date_range_inclusive, parse_dates_csv
from .path_resolver import find_crop_b_root
from .scanner import scan


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mavin_fetcher",
        description="Fetch Crop_B images by class, or summarize CSV results."
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    # ---- fetch subcommand ----
    pf = sub.add_parser("fetch", help="Fetch images from Crop_B and merge into one output folder.")

    mode = pf.add_mutually_exclusive_group(required=True)
    mode.add_argument("--date", help="Single date (YYYY-MM-DD)")
    mode.add_argument("--range", nargs=2, metavar=("START", "END"), help="Date range inclusive (YYYY-MM-DD YYYY-MM-DD)")
    mode.add_argument("--dates", help="Comma-separated list of dates (YYYY-MM-DD,YYYY-MM-DD,...)")

    pf.add_argument("--out", required=True, help="Output directory (class folders will be created here)")
    pf.add_argument("--model", default=DEFAULT_MODEL, help=f"Model folder under Files\\Image (default: {DEFAULT_MODEL})")
    pf.add_argument(
        "--drives",
        default=",".join(DEFAULT_DRIVES),
        help="Comma-separated drive letters to scan (default: E..Z)"
    )
    pf.add_argument(
        "--include-activemap",
        action="store_true",
        help="Also copy the paired ActiveMap for each SourceMap (if it exists)."
    )

    # ---- summary subcommand ----
    ps = sub.add_parser("summary", help="Summarize one or more CSV/XLSX result files.")
    ps.add_argument(
        "--csv",
        nargs="+",
        required=True,
        help="One or more CSV/XLSX result files to summarize."
    )
    ps.add_argument(
        "--top",
        type=int,
        default=20,
        help="How many top classes to show (default: 20)."
    )

    return p


def parse_drives(s: str) -> Sequence[str]:
    parts = [x.strip() for x in s.split(",") if x.strip()]
    return parts if parts else list(DEFAULT_DRIVES)


def resolve_days(args) -> list:
    if getattr(args, "date", None):
        return [parse_ymd(args.date)]
    if getattr(args, "range", None):
        start = parse_ymd(args.range[0])
        end = parse_ymd(args.range[1])
        return date_range_inclusive(start, end)
    if getattr(args, "dates", None):
        seen = set()
        out = []
        for d in parse_dates_csv(args.dates):
            if d not in seen:
                seen.add(d)
                out.append(d)
        return out
    raise ValueError("No date mode selected (should be prevented by argparse).")


def run_summary(args) -> int:
    csv_paths = [Path(x).expanduser().resolve() for x in args.csv]
    s = summarize_csv(csv_paths)
    print(format_summary(s, top_n=int(args.top)))
    return 0


def run_fetch(args) -> int:
    out_dir = Path(args.out).expanduser().resolve()
    model = args.model.strip()
    drives = parse_drives(args.drives)
    days = resolve_days(args)
    include_active = bool(args.include_activemap)

    print(f"[INFO] Days selected: {len(days)}")
    print(f"[INFO] Model: {model}")
    print(f"[INFO] Output: {out_dir}")
    print(f"[INFO] Drives: {', '.join(drives)}")
    print(f"[INFO] Include ActiveMap: {include_active}")

    total_files = 0
    total_overwritten = 0
    missing_days = 0

    total_missing_active = 0
    total_included_active = 0

    for day in days:
        found = find_crop_b_root(model=model, day=day, drives=drives)
        if not found:
            print(f"[WARN] Missing Crop_B folder for {day} (model={model})")
            missing_days += 1
            continue

        print(f"[OK] {day} -> {found.drive}: {found.path}")

        scan_result = scan(found.path, include_activemap=include_active)
        classes = scan_result.files_by_class

        total_missing_active += scan_result.missing_activemap_count
        total_included_active += scan_result.included_activemap_count

        if not classes:
            print("  [WARN] No class folders found (or only excluded OK folders existed).")
            continue

        for class_name, files in classes.items():
            if not files:
                continue
            dest = out_dir / class_name
            copied, overwritten = copy_overwrite(files, dest)
            total_files += copied
            total_overwritten += overwritten
            print(f"  - {class_name}: copied {copied} (overwrote {overwritten})")

    if include_active:
        print(f"[INFO] ActiveMap included: {total_included_active} | missing pairs: {total_missing_active}")

    print(f"[DONE] Total copied: {total_files} | Total overwrote: {total_overwritten} | Missing days: {missing_days}")
    return 0 if missing_days == 0 else 1


def main() -> int:
    args = build_parser().parse_args()

    if args.cmd == "summary":
        return run_summary(args)
    if args.cmd == "fetch":
        return run_fetch(args)

    print("[ERROR] Unknown command.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
