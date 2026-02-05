from __future__ import annotations

from pathlib import Path

from remote_paths import RemoteVisionPC
from preference_reader import RecipeInfo
from vision.base import VisionAdapter, VisionContext


class WeldingAdapter(VisionAdapter):
    """
    Welding uses \\IP\<share>\VisionPC\Setting\Preference.ini
    and \\IP\<share>\VisionPC\Recipe\<3digit>\<RecipeName>
    """

    def preference_ini(self, remote: RemoteVisionPC) -> Path:
        return remote.preference_ini

    def recipe_file(self, remote: RemoteVisionPC, info: RecipeInfo) -> Path:
        return remote.recipe_file(info.recipe_id_3digit, info.recipe_name)

    def kickout_xlsx(self, ctx: VisionContext, info: RecipeInfo) -> Path:
        # KickoutLists/Welding/<RecipeName>.xlsx
        return ctx.kickout_dir / f"{info.recipe_name}.xlsx"