from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class PcInfo:
    key: str
    line: str
    polarity: str
    ip: str


def load_pcs(config_path: Path) -> List[PcInfo]:
    if not config_path.exists():
        raise FileNotFoundError(f"PC config not found: {config_path}")

    data = json.loads(config_path.read_text(encoding="utf-8"))
    pcs: List[PcInfo] = []
    for key, v in data.items():
        pcs.append(PcInfo(
            key=key,
            line=str(v.get("line", "")),
            polarity=str(v.get("polarity", "")),
            ip=str(v.get("ip", "")),
        ))
    pcs.sort(key=lambda p: (p.line, p.polarity, p.key))
    return pcs
