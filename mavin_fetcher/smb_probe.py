from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Optional


DEFAULT_SMB_PORT = 445
DEFAULT_TIMEOUT_SEC = 0.5  # keep this short to avoid hanging on offline PCs


def can_connect_smb(ip: str, timeout_sec: float = DEFAULT_TIMEOUT_SEC) -> bool:
    """
    Fast reachability probe: TCP connect to port 445.
    """
    try:
        with socket.create_connection((ip, DEFAULT_SMB_PORT), timeout=timeout_sec):
            return True
    except Exception:
        return False
