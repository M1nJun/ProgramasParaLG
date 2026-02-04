from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RemoteVisionPC:
    ip: str
    share_name: str = "C"  # custom share confirmed by you

    @property
    def visionpc_root(self) -> Path:
        # \\10.73.103.71\C\VisionPC
        return Path(rf"\\{self.ip}\{self.share_name}\VisionPC")

    @property
    def preference_ini(self) -> Path:
        return self.visionpc_root / "Setting" / "Preference.ini"

    def recipe_file(self, recipe_id_3digit: str, recipe_name: str) -> Path:
        return self.visionpc_root / "Recipe" / recipe_id_3digit / recipe_name
