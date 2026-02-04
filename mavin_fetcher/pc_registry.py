from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .runtime_paths import find_file_near_exe


@dataclass(frozen=True)
class PcInfo:
    key: str
    line: str
    polarity: str
    ip: str


class PcRegistryError(RuntimeError):
    pass


def default_pcs_json_path() -> Path:
    return find_file_near_exe("pcs.json")


def load_registry(path: Optional[Path] = None) -> Dict[str, PcInfo]:
    """
    Loads pcs.json (next to exe by default). Returns dict key -> PcInfo.
    """
    p = path or default_pcs_json_path()
    if not p.exists():
        raise PcRegistryError(f"pcs.json not found: {p}")

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise PcRegistryError(f"Failed to parse pcs.json: {p}\n{e}") from e

    if not isinstance(data, dict):
        raise PcRegistryError("pcs.json root must be an object/dict.")

    out: Dict[str, PcInfo] = {}
    for key, obj in data.items():
        if not isinstance(obj, dict):
            continue
        line = str(obj.get("line", "")).strip()
        polarity = str(obj.get("polarity", "")).strip()
        ip = str(obj.get("ip", "")).strip()
        if not key or not ip:
            continue
        out[key] = PcInfo(key=str(key), line=line, polarity=polarity, ip=ip)

    if not out:
        raise PcRegistryError("pcs.json loaded but contains no usable PCs.")

    return out


def sorted_keys(reg: Dict[str, PcInfo]) -> List[str]:
    return sorted(reg.keys(), key=lambda s: s.lower())
