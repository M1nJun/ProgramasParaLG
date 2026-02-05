from __future__ import annotations

from pathlib import Path
from typing import List

from config.pcs_schema import PCEntry, PCConfigError
from config.pcs_loader import load_pcs_config


# Backward compatible name used by current UI code
def load_pcs_config_nested(json_path: Path, vision_mode: str) -> List[PCEntry]:
    return load_pcs_config(json_path, vision_mode)