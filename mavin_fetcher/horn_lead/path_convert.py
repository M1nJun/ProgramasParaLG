from __future__ import annotations

import re
from pathlib import Path, PureWindowsPath
from typing import Optional

_DRIVE_RE = re.compile(r"^(?P<drive>[A-Za-z]):\\")  # e.g. F:\...

def candidate_share_names(drive_letter: str) -> list[str]:
    """
    Possible SMB share names for a drive.
    Plants sometimes expose drives as:
      - E
      - E$
      - $E
    """
    d = (drive_letter or "").strip().upper()
    if not d:
        return []
    return [d, f"{d}$", f"${d}"]

def resolve_drive_root(ip: str, drive_letter: str) -> Optional[Path]:
    ip = (ip or "").strip()
    d = (drive_letter or "").strip().upper()
    for share in candidate_share_names(d):
        root = Path(rf"\\{ip}\{share}")
        try:
            if root.exists():
                return root
        except Exception:
            continue
    return None

def local_path_to_unc(ip: str, local_path: str) -> Path:
    """
    Convert a local Windows path (e.g., F:\\Files\\Image\\...) to a UNC Path.
    If already UNC, return it as Path.
    """
    p = (local_path or "").strip()
    m = _DRIVE_RE.match(p)
    if not m:
        if p.startswith("\\\\"):
            return Path(p)
        raise ValueError(f"Not an absolute drive path: {local_path!r}")

    drive = m.group("drive").upper()
    root = resolve_drive_root(ip, drive)
    if root is None:
        raise FileNotFoundError(f"No accessible share for drive {drive} on {ip}")

    w = PureWindowsPath(p)
    rel_parts = list(w.parts)[1:]  # drop 'F:\'
    out = root
    for part in rel_parts:
        out = out / part
    return out