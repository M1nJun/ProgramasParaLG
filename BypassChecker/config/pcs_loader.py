from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .pcs_schema import PCEntry, PCConfigError


def _read_json(json_path: Path) -> Dict[str, Any]:
    if not json_path.exists():
        raise PCConfigError(f"pcs.json not found: {json_path}")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise PCConfigError(f"Failed to read pcs.json: {e}")

    if not isinstance(data, dict):
        raise PCConfigError("pcs.json must be a JSON object at top-level.")
    return data


def _stable_sort(pcs: List[PCEntry]) -> List[PCEntry]:
    pcs.sort(key=lambda x: (x.line, x.polarity, x.key))
    return pcs


def load_pcs_config(json_path: Path, vision_mode: str) -> List[PCEntry]:
    """
    vision_mode: "Welding" or "Lead" (case-insensitive)

    Recommended schema:
      {
        "version": 1,
        "defaults": {"share_name": "C"},
        "lines": {
          "3-1": {
            "welding": {
              "(-)": {"ip": "...", "enabled": true},
              "(+)": {"ip": "...", "enabled": true}
            },
            "lead": {"ip": "...", "enabled": true}
          }
        }
      }

    Backward compatible:
      - nested: {"welding": {...}, "lead": {...}}
      - legacy flat welding-only: {"3-1 (-)": {"line":"3-1","polarity":"(-)","ip":"..."}}
    """
    mode_key = vision_mode.strip().lower()
    if mode_key not in ("welding", "lead"):
        raise PCConfigError(f"Unknown vision_mode: {vision_mode}")

    data = _read_json(json_path)

    # -------------------------
    # NEW schema (versioned)
    # -------------------------
    if "lines" in data and isinstance(data.get("lines"), dict):
        defaults = data.get("defaults") if isinstance(data.get("defaults"), dict) else {}
        default_share = str(defaults.get("share_name", "C")).strip() or "C"

        out: List[PCEntry] = []
        lines_obj: Dict[str, Any] = data["lines"]

        for line, block in lines_obj.items():
            if not isinstance(block, dict):
                continue

            if mode_key == "welding":
                weld = block.get("welding")
                if not isinstance(weld, dict):
                    continue

                for pol in ("(-)", "(+)"):
                    ent = weld.get(pol)
                    if ent is None:
                        continue

                    if isinstance(ent, str):
                        ip = ent.strip()
                        enabled = True
                    elif isinstance(ent, dict):
                        ip = str(ent.get("ip", "")).strip()
                        enabled = bool(ent.get("enabled", True))
                    else:
                        continue

                    if not ip or not enabled:
                        continue

                    key = f"{line} {pol}"
                    out.append(
                        PCEntry(
                            key=key,
                            line=str(line),
                            polarity=pol,
                            ip=ip,
                            share_name=default_share,
                            enabled=True,
                        )
                    )

            else:  # lead
                lead = block.get("lead")
                if lead is None:
                    continue

                if isinstance(lead, str):
                    ip = lead.strip()
                    enabled = True
                elif isinstance(lead, dict):
                    ip = str(lead.get("ip", "")).strip()
                    enabled = bool(lead.get("enabled", True))
                else:
                    continue

                if not ip or not enabled:
                    continue

                out.append(
                    PCEntry(
                        key=str(line),
                        line=str(line),
                        polarity="",
                        ip=ip,
                        share_name=default_share,
                        enabled=True,
                    )
                )

        if not out:
            raise PCConfigError(f"No valid PC entries found for '{mode_key}' in pcs.json.")
        return _stable_sort(out)

    # -------------------------
    # Older nested schema
    # -------------------------
    if mode_key in data and isinstance(data.get(mode_key), dict):
        mode_block: Dict[str, Any] = data[mode_key]
        out: List[PCEntry] = []

        if mode_key == "welding":
            for line, obj in mode_block.items():
                if not isinstance(obj, dict):
                    continue
                for pol in ("(-)", "(+)"):
                    ip = str(obj.get(pol, "")).strip()
                    if not ip:
                        continue
                    key = f"{line} {pol}"
                    out.append(PCEntry(key=key, line=str(line), polarity=pol, ip=ip, share_name="C", enabled=True))
        else:
            for line, obj in mode_block.items():
                if not isinstance(obj, dict):
                    continue
                ip = str(obj.get("ip", "")).strip()
                if not ip:
                    continue
                out.append(PCEntry(key=str(line), line=str(line), polarity="", ip=ip, share_name="C", enabled=True))

        if not out:
            raise PCConfigError(f"No valid PC entries found for '{mode_key}' in pcs.json.")
        return _stable_sort(out)

    # -------------------------
    # Older flat welding-only schema
    # -------------------------
    if mode_key == "lead":
        raise PCConfigError("pcs.json is in legacy welding-only format; no Lead PCs present.")

    out: List[PCEntry] = []
    for key, obj in data.items():
        if not isinstance(obj, dict):
            continue
        line = str(obj.get("line", "")).strip()
        pol = str(obj.get("polarity", "")).strip()
        ip = str(obj.get("ip", "")).strip()
        if not line or not pol or not ip:
            continue
        out.append(PCEntry(key=str(key), line=line, polarity=pol, ip=ip, share_name="C", enabled=True))

    if not out:
        raise PCConfigError("No valid welding PC entries found in pcs.json.")
    return _stable_sort(out)