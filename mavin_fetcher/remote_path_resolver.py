from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, List

from .area_spec import AreaSpec, AREA_B, area_from_id
from .pc_registry import PcInfo
from .smb_probe import can_connect_smb, DEFAULT_TIMEOUT_SEC
from .smb_paths import IMAGE_DRIVES, image_base, crop_root


@dataclass(frozen=True)
class RemoteCropRoot:
    pc_key: str
    ip: str
    drive: str
    area_id: str          # "A" or "B"
    path: Path


# -------------------------
# New generic implementation
# -------------------------

def find_remote_crop_roots(
    *,
    pc: PcInfo,
    model: str,
    day: date,
    area: AreaSpec,
    drives: Iterable[str] = IMAGE_DRIVES,
    probe_first: bool = True,
    probe_timeout_sec: float = DEFAULT_TIMEOUT_SEC,
) -> List[RemoteCropRoot]:
    """
    Returns 0..N crop roots found across E/F/G for that PC/day/model/area.
    """
    if probe_first and not can_connect_smb(pc.ip, timeout_sec=probe_timeout_sec):
        return []

    found: List[RemoteCropRoot] = []
    for d in drives:
        base = image_base(pc.ip, d)
        root = crop_root(base, model, day, area)
        try:
            if root.exists() and root.is_dir():
                found.append(
                    RemoteCropRoot(
                        pc_key=pc.key,
                        ip=pc.ip,
                        drive=d,
                        area_id=area.area_id,
                        path=root,
                    )
                )
        except Exception:
            # network permission/offline edge; treat as not found
            continue

    return found


# --------------------------------
# Backwards-compatible B-only API
# --------------------------------

@dataclass(frozen=True)
class RemoteCropBRoot:
    pc_key: str
    ip: str
    drive: str
    path: Path


def find_remote_crop_b_roots(
    *,
    pc: PcInfo,
    model: str,
    day: date,
    drives: Iterable[str] = IMAGE_DRIVES,
    probe_first: bool = True,
    probe_timeout_sec: float = DEFAULT_TIMEOUT_SEC,
) -> List[RemoteCropBRoot]:
    """
    Legacy wrapper to preserve existing Crop_B behavior.
    """
    roots = find_remote_crop_roots(
        pc=pc,
        model=model,
        day=day,
        area=AREA_B,
        drives=drives,
        probe_first=probe_first,
        probe_timeout_sec=probe_timeout_sec,
    )
    return [RemoteCropBRoot(pc_key=r.pc_key, ip=r.ip, drive=r.drive, path=r.path) for r in roots]


# Convenience wrapper for A (optional, will be used later)
def find_remote_crop_a_roots(
    *,
    pc: PcInfo,
    model: str,
    day: date,
    drives: Iterable[str] = IMAGE_DRIVES,
    probe_first: bool = True,
    probe_timeout_sec: float = DEFAULT_TIMEOUT_SEC,
) -> List[RemoteCropRoot]:
    return find_remote_crop_roots(
        pc=pc,
        model=model,
        day=day,
        area=area_from_id("A"),
        drives=drives,
        probe_first=probe_first,
        probe_timeout_sec=probe_timeout_sec,
    )