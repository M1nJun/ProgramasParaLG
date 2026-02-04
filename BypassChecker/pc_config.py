from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class PCEntry:
    key: str
    line: str
    polarity: str   # "(-)", "(+)" or "" for lead
    ip: str


class PCConfigError(Exception):
    pass


def load_pcs_config_nested(json_path: Path, vision_mode: str) -> List[PCEntry]:
    """
    vision_mode: "Welding" or "Lead"
    Expects nested pcs.json:
      {
        "welding": { "3-1": {"(-)": "ip", "(+)":"ip"} ... },
        "lead": { "3-1": {"ip": "ip"} ... }
      }
    """
    if not json_path.exists():
        raise PCConfigError(f"pcs.json not found: {json_path}")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise PCConfigError(f"Failed to read pcs.json: {e}")

    if not isinstance(data, dict):
        raise PCConfigError("pcs.json must be a JSON object at top-level.")

    mode_key = vision_mode.strip().lower()
    if mode_key not in data:
        raise PCConfigError(f"pcs.json missing key '{mode_key}'")

    mode_block = data.get(mode_key)
    if not isinstance(mode_block, dict):
        raise PCConfigError(f"pcs.json '{mode_key}' must be an object")

    out: List[PCEntry] = []

    if mode_key == "welding":
        # line -> { "(-)": ip, "(+)": ip }
        for line, obj in mode_block.items():
            if not isinstance(obj, dict):
                continue
            for pol in ["(-)", "(+)"]:
                ip = str(obj.get(pol, "")).strip()
                if not ip:
                    continue
                key = f"{line} {pol}"
                out.append(PCEntry(key=key, line=str(line), polarity=pol, ip=ip))

    elif mode_key == "lead":
        # line -> { "ip": ip }
        for line, obj in mode_block.items():
            if not isinstance(obj, dict):
                continue
            ip = str(obj.get("ip", "")).strip()
            if not ip:
                continue
            key = str(line)
            out.append(PCEntry(key=key, line=str(line), polarity="", ip=ip))

    if not out:
        raise PCConfigError(f"No valid PC entries found for '{mode_key}' in pcs.json.")

    # stable order by line then polarity
    out.sort(key=lambda x: (x.line, x.polarity))
    return out
