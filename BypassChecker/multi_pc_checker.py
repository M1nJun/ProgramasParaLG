# multi_pc_checker.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from pc_config import PCEntry
from remote_paths import RemoteVisionPC

from preference_reader import read_recipe_info
from recipe_parser import parse_recipe_measures
from kickout_loader import load_kickout_list_xlsx
from checker import check_kickout, CheckReport

from vision.base import VisionContext
from vision.factory import get_adapter


@dataclass(frozen=True)
class PCCheckResult:
    pc: PCEntry
    report: Optional[CheckReport]
    error: Optional[str]


def check_one_pc(pc: PCEntry, kickout_dir: Path, vision_mode: str) -> PCCheckResult:
    try:
        adapter = get_adapter(vision_mode)
        ctx = VisionContext(name=vision_mode, kickout_dir=kickout_dir)

        remote = RemoteVisionPC(ip=pc.ip, share_name=pc.share_name)

        pref_path = adapter.preference_ini(remote)

        recipe_info = read_recipe_info(pref_path, vision_mode=vision_mode)
        info = recipe_info  # compatibility alias: old code expects `info`

        recipe_path = adapter.recipe_file(remote, info)
        measures = parse_recipe_measures(recipe_path)

        kickout_path = adapter.kickout_xlsx(ctx, info)
        kickout = load_kickout_list_xlsx(kickout_path, sheet_name=None)

        report = check_kickout(
            measures=measures,
            kickout=kickout,
            recipe_name=info.recipe_name,
            recipe_id_3digit=info.recipe_id_3digit,
            kickout_filename=kickout_path.name,
        )

        return PCCheckResult(pc=pc, report=report, error=None)

    except Exception as e:
        return PCCheckResult(pc=pc, report=None, error=str(e))


def check_all_pcs(pcs: List[PCEntry], kickout_dir: Path, vision_mode: str) -> List[PCCheckResult]:
    return [check_one_pc(pc, kickout_dir, vision_mode) for pc in pcs]