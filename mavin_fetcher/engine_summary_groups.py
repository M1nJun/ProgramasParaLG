from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

# Matches: "#5-2 WELDING VISION(-)"  OR  "#3-2 WELDING VISION(+)"
_LINE_RE = re.compile(r"#(?P<line>\d+-\d+)\s+WELDING\s+VISION\((?P<pol>[+-])\)", re.IGNORECASE)


@dataclass(frozen=True)
class GroupKey:
    pc: str
    line: str  # "5-2 (-)"


def extract_group_key(path: Path) -> GroupKey:
    name = path.name

    # Our cached CSV names are like: "PC05__#5-2 WELDING VISION(-)_JF2_20260127.csv"
    pc = ""
    if "__" in name:
        pc = name.split("__", 1)[0].strip()

    line = ""
    m = _LINE_RE.search(name)
    if m:
        line = f"{m.group('line')} ({m.group('pol')})"

    return GroupKey(pc=pc, line=line)


def group_paths(paths: List[Path]) -> Tuple[Dict[str, List[Path]], Dict[str, List[Path]]]:
    """
    Returns:
      by_pc:   {pc_key: [paths...]}
      by_line: {line_key: [paths...]}   e.g. "5-2 (-)"
    """
    by_pc: Dict[str, List[Path]] = {}
    by_line: Dict[str, List[Path]] = {}

    for p in paths:
        g = extract_group_key(p)
        if g.pc:
            by_pc.setdefault(g.pc, []).append(p)
        if g.line:
            by_line.setdefault(g.line, []).append(p)

    return by_pc, by_line