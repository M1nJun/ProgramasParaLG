from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from remote_paths import RemoteVisionPC
from preference_reader import RecipeInfo


@dataclass(frozen=True)
class VisionContext:
    """
    Paths that depend on vision type (Welding vs Lead).
    """
    name: str                # "Welding" or "Lead"
    kickout_dir: Path        # e.g. KickoutLists/Welding or KickoutLists/Lead


class VisionAdapter(Protocol):
    """
    Vision-specific behaviors: how to locate files and where to load kickout lists.
    """

    def preference_ini(self, remote: RemoteVisionPC) -> Path:
        ...

    def recipe_file(self, remote: RemoteVisionPC, info: RecipeInfo) -> Path:
        ...

    def kickout_xlsx(self, ctx: VisionContext, info: RecipeInfo) -> Path:
        ...