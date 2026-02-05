from __future__ import annotations

import traceback
from pathlib import Path


def ensure_dir(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def append_crash_log(reports_dir: Path, context: str, exc: BaseException) -> None:
    try:
        ensure_dir(reports_dir)
        log_path = reports_dir / "ui_crash.log"
        with log_path.open("a", encoding="utf-8") as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"[{context}] {type(exc).__name__}: {exc}\n")
            f.write(traceback.format_exc())
    except Exception:
        pass