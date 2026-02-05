from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PCEntry:
    key: str
    line: str
    polarity: str   # "(-)", "(+)" or "" (Lead)
    ip: str
    share_name: str
    enabled: bool = True


class PCConfigError(Exception):
    pass