from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Tuple

from PyQt6.QtCore import QThread, pyqtSignal

from mavin_fetcher.pc_registry import load_registry, PcRegistryError


def _unc_dir(ip: str) -> Path:
    # confirmed format: \\IP\D\Files\Data\Result\Day
    return Path(f"\\\\{ip}\\D\\Files\\Data\\Result\\Day")


def _is_ignored_csv(p: Path) -> bool:
    return p.name.lower().endswith("_defect.csv")


def _find_csvs(remote_dir: Path, model: str, d: date) -> List[Path]:
    yyyymmdd = d.strftime("%Y%m%d")
    model = (model or "").strip()
    if not model:
        return []

    pat_base = f"#*-* WELDING VISION(*)_{model}_{yyyymmdd}.csv"
    pat_suffix = f"#*-* WELDING VISION(*)_{model}_{yyyymmdd}_*.csv"

    hits = list(remote_dir.glob(pat_base)) + list(remote_dir.glob(pat_suffix))
    hits = [p for p in hits if p.is_file() and not _is_ignored_csv(p)]

    # base first then numeric suffix
    def sort_key(p: Path) -> Tuple[int, str]:
        name = p.name
        stem = name[:-4] if name.lower().endswith(".csv") else name
        n = 0
        if "_" in stem:
            tail = stem.rsplit("_", 1)[-1]
            if tail.isdigit():
                n = int(tail)
        return (n, name.lower())

    return sorted({p for p in hits}, key=sort_key)


@dataclass(frozen=True)
class RemoteCsvFetchConfig:
    out_dir: Path
    model: str
    days: List[date]
    selected_pc_keys: List[str]


class RemoteCsvFetchWorker(QThread):
    progress = pyqtSignal(int, int)    # done_steps, total_steps
    progress_pct = pyqtSignal(int)     # 0..100
    log = pyqtSignal(str)
    done = pyqtSignal(bool, str, object)  # success, message, cached_paths(list[str])

    def __init__(self, cfg: RemoteCsvFetchConfig):
        super().__init__()
        self.cfg = cfg
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        try:
            try:
                reg = load_registry()
            except PcRegistryError as e:
                self.done.emit(False, f"pcs.json error:\n{e}", [])
                return

            pcs = [reg[k] for k in (self.cfg.selected_pc_keys or []) if k in reg]
            if not pcs:
                self.done.emit(False, "No valid PCs selected (check pcs.json and selection).", [])
                return

            cache_dir = self.cfg.out_dir / "_summary_csv_cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            self.log.emit(f"[CSV] Cache dir: {cache_dir}")

            total_steps = len(pcs) * max(1, len(self.cfg.days))
            done_steps = 0
            self.progress.emit(done_steps, total_steps)
            self.progress_pct.emit(0)

            cached: List[Path] = []
            pcs_missing_dir = 0
            pcs_no_csv = 0
            copied = 0
            overwritten = 0

            for pc in pcs:
                if self._cancel:
                    self.done.emit(False, "Cancelled.", [])
                    return

                remote_dir = _unc_dir(pc.ip)
                if not remote_dir.exists():
                    pcs_missing_dir += 1
                    self.log.emit(f"[CSV][WARN] Missing remote dir: {remote_dir} ({pc.key})")
                    done_steps += len(self.cfg.days)
                    self._emit_progress(done_steps, total_steps)
                    continue

                pc_found_any = False

                for d in self.cfg.days:
                    if self._cancel:
                        self.done.emit(False, "Cancelled.", [])
                        return

                    found = _find_csvs(remote_dir, self.cfg.model, d)
                    if found:
                        pc_found_any = True
                        self.log.emit(f"[CSV] {pc.key} {d}: found {len(found)} file(s)")

                    for src in found:
                        dst = cache_dir / f"{pc.key}__{src.name}"
                        if dst.exists():
                            overwritten += 1
                        try:
                            dst.write_bytes(src.read_bytes())
                            copied += 1
                            cached.append(dst)
                        except Exception as e:
                            self.log.emit(f"[CSV][WARN] Copy failed: {src} -> {dst} ({e})")

                    done_steps += 1
                    self._emit_progress(done_steps, total_steps)

                if not pc_found_any:
                    pcs_no_csv += 1
                    self.log.emit(f"[CSV][INFO] {pc.key}: no CSV matched for selected day(s)/model.")

            uniq: List[Path] = []
            seen = set()
            for p in cached:
                rp = str(p.resolve())
                if rp not in seen:
                    seen.add(rp)
                    uniq.append(p)

            msg = (
                f"CSV fetch done. cached={len(uniq)}, copied={copied}, overwritten={overwritten}, "
                f"pcs_missing_dir={pcs_missing_dir}, pcs_no_csv={pcs_no_csv}"
            )
            self.done.emit(True, msg, [str(p) for p in uniq])

        except Exception as e:
            self.done.emit(False, f"Error: {e}", [])

    def _emit_progress(self, done: int, total: int) -> None:
        pct = int((done / total) * 100) if total else 0
        self.progress.emit(done, total)
        self.progress_pct.emit(pct)