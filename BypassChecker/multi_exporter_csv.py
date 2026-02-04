from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import List

from multi_pc_checker import PCCheckResult


def export_all_pcs_summary_csv(results: List[PCCheckResult], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"bypass_all_pcs_summary_{ts}.csv"

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["GeneratedAt", datetime.now().isoformat()])
        w.writerow([])
        w.writerow([
            "Status",
            "PC",
            "IP",
            "Line",
            "Polarity",
            "Recipe",
            "Folder",
            "FailCount",
            "MissingCount",
            "BypassedCount",
            "Error",
        ])

        for r in results:
            if r.error or r.report is None:
                w.writerow([
                    "ERROR",
                    r.pc.key,
                    r.pc.ip,
                    r.pc.line,
                    r.pc.polarity,
                    "",
                    "",
                    "",
                    "",
                    "",
                    r.error or "Unknown error",
                ])
                continue

            rep = r.report
            fail_count = sum(1 for x in rep.rows if not x.is_pass)
            missing_count = sum(1 for x in rep.rows if x.is_missing)
            bypassed_count = sum(1 for x in rep.rows if x.has_bypassed)

            status = "PASS" if fail_count == 0 else "FAIL"

            w.writerow([
                status,
                r.pc.key,
                r.pc.ip,
                r.pc.line,
                r.pc.polarity,
                rep.recipe_name,
                rep.recipe_id_3digit,
                fail_count,
                missing_count,
                bypassed_count,
                "",
            ])

    return out_path
