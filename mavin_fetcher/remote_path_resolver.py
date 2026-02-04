from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional

from .pc_registry import PcInfo
from .smb_probe import can_connect_smb, DEFAULT_TIMEOUT_SEC
from .smb_paths import IMAGE_DRIVES, image_base, crop_b_root


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
    Returns 0..N crop_b roots found across E/F/G for that PC/day/model.
    """
    if probe_first and not can_connect_smb(pc.ip, timeout_sec=probe_timeout_sec):
        return []

    found: List[RemoteCropBRoot] = []
    for d in drives:
        base = image_base(pc.ip, d)
        root = crop_b_root(base, model, day)
        try:
            if root.exists() and root.is_dir():
                found.append(RemoteCropBRoot(pc_key=pc.key, ip=pc.ip, drive=d, path=root))
        except Exception:
            # network permission/offline edge; treat as not found
            continue

    return found
