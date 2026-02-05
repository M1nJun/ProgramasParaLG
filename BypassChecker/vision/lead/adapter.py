from __future__ import annotations

from pathlib import Path

from remote_paths import RemoteVisionPC
from preference_reader import RecipeInfo
from vision.base import VisionAdapter, VisionContext


class LeadAdapter(VisionAdapter):
    """
    For now we assume Lead has the SAME VisionPC layout as Welding.
    If Lead differs later (different folder/recipe), we change only this adapter.
    """

    def preference_ini(self, remote: RemoteVisionPC) -> Path:
        return remote.preference_ini

    def recipe_file(self, remote: RemoteVisionPC, info: RecipeInfo) -> Path:
        return remote.recipe_file(info.recipe_id_3digit, info.recipe_name)

    def kickout_xlsx(self, ctx: VisionContext, info: RecipeInfo) -> Path:
        # KickoutLists/Lead/<RecipeName>.xlsx
        return ctx.kickout_dir / f"{info.recipe_name}.xlsx"