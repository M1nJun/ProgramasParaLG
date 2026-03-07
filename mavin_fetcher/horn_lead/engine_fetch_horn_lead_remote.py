from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

from mavin_fetcher.csv_autofind import find_csvs_for_day
from mavin_fetcher.csv_reader import iter_rows
from mavin_fetcher.pc_registry import PcInfo

from .defect_rules import is_target_defect, side_from_defect, DefectHit
from .mavin_locator import find_mavin_root
from .path_convert import local_path_to_unc

_DEFECT_KEYS = ("JUDGE-DEFECT", "JUDGE_DEFECT")
_CELL_KEYS = ("CELL-ID", "CELL_ID")
_UP_IMG3_KEYS = ("UPPER_IMAGE-PATH-3", "UPPER_IMAGE_PATH_3")
_UP_OVL3_KEYS = ("UPPER_OVERLAY-IMAGE-PATH-3", "UPPER_OVERLAY_IMAGE_PATH_3")


def _get_first(row: Dict[str, str], keys: Iterable[str]) -> str:
    for k in keys:
        if k in row:
            return row.get(k, "") or ""
    return ""


_IDX_RE = re.compile(r"_(?P<i>\d+)_(?P<j>\d+)(?P<ovl>_overlay)?\.jpg$", re.IGNORECASE)


def _ensure_0_2_variant(p: str) -> str:
    """
    If the path ends with _i_j(.jpg or _overlay.jpg), rewrite to _0_2.
    This matches your requirement to avoid *_1_2, *_0_1, etc.
    """
    s = (p or "").strip()
    m = _IDX_RE.search(s)
    if not m:
        return s
    ovl = m.group("ovl") or ""
    return _IDX_RE.sub(f"_0_2{ovl}.jpg", s)


def _resolve_day_root(out_dir: Path, day_tag: str) -> Path:
    """
    Avoid duplicated YYYYMMDD folders.
    If the user already chose ...\\<YYYYMMDD> as out_dir, don't append day_tag again.
    """
    out_dir = Path(out_dir).expanduser().resolve()
    if out_dir.name == day_tag:
        return out_dir
    return out_dir / day_tag


@dataclass
class HornLeadStats:
    total_rows_scanned: int = 0
    total_hits: int = 0
    total_files_copied: int = 0
    total_files_overwritten: int = 0
    missing_files: List[str] = field(default_factory=list)
    missing_pcs: List[str] = field(default_factory=list)
    missing_mavin_roots: List[str] = field(default_factory=list)


def fetch_horn_lead_remote(
    *,
    pcs: List[PcInfo],
    days: List[date],
    out_dir: Path,
    model: str,
    csv_dir_local: str = r"D:\Files\Data\Result\Day",
    log: Optional[Callable[[str], None]] = None,
    progress: Optional[Callable[[int, int], None]] = None,
    is_cancelled: Optional[Callable[[], bool]] = None,
) -> HornLeadStats:
    """
    CSV-driven fetch for B_DIM/H_DIM defects.

    Output layout (Option A) - UPDATED:
      <out_dir>/<YYYYMMDD>/<DEFECT>/<CELL-ID>/
        (all images directly under CELL-ID, no DIST/HORNMARK/LEADEDGE subfolders)
    """
    def _log(msg: str) -> None:
        if log:
            log(msg)

    def _cancel() -> bool:
        return bool(is_cancelled() if is_cancelled else False)

    out_dir = Path(out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = HornLeadStats()

    done = 0
    total = 0  # dynamic: based on how many hits we discover

    def _bump_progress() -> None:
        if progress:
            progress(done, max(total, 1))

    def _copy_one(src: Path, dst_dir: Path) -> None:
        nonlocal done
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / src.name
        try:
            existed = dst.exists()
            shutil.copy2(src, dst)
            stats.total_files_copied += 1
            if existed:
                stats.total_files_overwritten += 1
            done += 1
            _bump_progress()
        except Exception as e:
            stats.missing_files.append(f"{src} ({e})")
            _log(f"[MISS] {src} ({e})")

    for pc in pcs:
        if _cancel():
            _log("[INFO] Cancelled.")
            return stats

        ip = pc.ip
        pc_key = pc.key

        # Remote CSV dir via UNC
        try:
            csv_dir = local_path_to_unc(ip, csv_dir_local)
        except Exception as e:
            stats.missing_pcs.append(pc_key)
            _log(f"[PC] {pc_key} ({ip}) CSV share not accessible: {e}")
            continue

        for day in days:
            if _cancel():
                _log("[INFO] Cancelled.")
                return stats

            day_tag = day.strftime("%Y%m%d")
            _log(f"[PC] {pc_key} {day_tag}: scanning CSVs...")

            try:
                csvs = find_csvs_for_day(csv_dir, model, day)
            except Exception as e:
                _log(f"[WARN] {pc_key} {day_tag}: CSV search error: {e}")
                continue

            if not csvs:
                _log(f"[WARN] {pc_key} {day_tag}: no CSVs found")
                continue

            # Find Mavin root once per pc/day
            mavin_root = find_mavin_root(ip=ip, model=model, day=day)
            if mavin_root is None:
                stats.missing_mavin_roots.append(f"{pc_key}:{day_tag}")
                _log(f"[WARN] {pc_key} {day_tag}: Mavin folder not found on any drive")

            horn_dir = (mavin_root / "HORNMARK") if mavin_root else None
            lead_dir = (mavin_root / "LEADEDGE") if mavin_root else None

            for csv_path in csvs:
                if _cancel():
                    _log("[INFO] Cancelled.")
                    return stats

                _log(f"[CSV] {csv_path}")

                for row in iter_rows(csv_path):
                    stats.total_rows_scanned += 1

                    defect = _get_first(row, _DEFECT_KEYS)
                    if not is_target_defect(defect):
                        continue

                    cell_id = _get_first(row, _CELL_KEYS).strip()
                    if not cell_id:
                        continue

                    upper_img = _ensure_0_2_variant(_get_first(row, _UP_IMG3_KEYS))
                    upper_ovl = _ensure_0_2_variant(_get_first(row, _UP_OVL3_KEYS))
                    if not upper_img or not upper_ovl:
                        continue

                    side = side_from_defect(defect)

                    hit = DefectHit(
                        defect=defect.strip().upper(),
                        side=side,
                        cell_id=cell_id,
                        upper_img_path=upper_img,
                        upper_overlay_path=upper_ovl,
                    )

                    stats.total_hits += 1
                    total += 6  # expected files per hit

                    # UPDATED: avoid duplicated YYYYMMDD if out_dir already ends with it
                    day_root = _resolve_day_root(out_dir, day_tag)

                    # UPDATED: no DIST/HORNMARK/LEADEDGE subfolders — everything under CELL-ID
                    out_cell_dir = day_root / hit.defect / hit.cell_id

                    _log(f"[HIT] {pc_key} {day_tag} {hit.defect} {hit.cell_id} side={hit.side}")

                    # DIST images from CSV (forced to 0_2)
                    try:
                        src_img = local_path_to_unc(ip, hit.upper_img_path)
                        src_ovl = local_path_to_unc(ip, hit.upper_overlay_path)

                        if src_img.exists():
                            _copy_one(src_img, out_cell_dir)
                        else:
                            stats.missing_files.append(str(src_img))
                            _log(f"[MISS] {src_img}")

                        if src_ovl.exists():
                            _copy_one(src_ovl, out_cell_dir)
                        else:
                            stats.missing_files.append(str(src_ovl))
                            _log(f"[MISS] {src_ovl}")

                    except Exception as e:
                        stats.missing_files.append(f"DIST({hit.cell_id}): {e}")
                        _log(f"[MISS] DIST paths error for {hit.cell_id}: {e}")

                    # HORNMARK files
                    if horn_dir and horn_dir.exists():
                        horn_jpg = list(horn_dir.glob(f"{hit.cell_id}_*HORNMARK_{hit.side}*_SourceImg.jpg"))
                        horn_msk = list(horn_dir.glob(f"{hit.cell_id}_*HORNMARK_{hit.side}*_SourceImg_mask.png"))

                        if horn_jpg:
                            _copy_one(horn_jpg[0], out_cell_dir)
                        else:
                            stats.missing_files.append(f"{horn_dir} :: {hit.cell_id} HORNMARK_{hit.side} jpg")
                            _log(f"[MISS] HORNMARK jpg for {hit.cell_id} side {hit.side}")

                        if horn_msk:
                            _copy_one(horn_msk[0], out_cell_dir)
                        else:
                            stats.missing_files.append(f"{horn_dir} :: {hit.cell_id} HORNMARK_{hit.side} mask")
                            _log(f"[MISS] HORNMARK mask for {hit.cell_id} side {hit.side}")

                    # LEADEDGE files
                    if lead_dir and lead_dir.exists():
                        lead_jpg = list(lead_dir.glob(f"{hit.cell_id}_*LEAD EDGE {hit.side}*_SourceImg.jpg"))
                        lead_png = list(lead_dir.glob(f"{hit.cell_id}_*LEAD EDGE {hit.side}*_SourceImg.png"))

                        if lead_jpg:
                            _copy_one(lead_jpg[0], out_cell_dir)
                        else:
                            stats.missing_files.append(f"{lead_dir} :: {hit.cell_id} LEAD EDGE {hit.side} jpg")
                            _log(f"[MISS] LEADEDGE jpg for {hit.cell_id} side {hit.side}")

                        if lead_png:
                            _copy_one(lead_png[0], out_cell_dir)
                        else:
                            stats.missing_files.append(f"{lead_dir} :: {hit.cell_id} LEAD EDGE {hit.side} png")
                            _log(f"[MISS] LEADEDGE png for {hit.cell_id} side {hit.side}")

    _log(
        "[DONE] horn/lead fetch finished: "
        f"hits={stats.total_hits}, copied={stats.total_files_copied}, overwritten={stats.total_files_overwritten}"
    )
    return stats