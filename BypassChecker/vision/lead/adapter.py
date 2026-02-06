# vision/lead/adapter.py
from __future__ import annotations

from pathlib import Path

from remote_paths import RemoteVisionPC
from preference_reader import RecipeInfo
from vision.base import VisionAdapter, VisionContext


class LeadAdapter(VisionAdapter):
    """
    Lead differs from Welding ONLY in how recipe measures are stored:
      - Lead uses:  C:\\VisionPC\\Recipe\\<RECIPE_ID>\\Recipe.json
    Everything else (kickout list name, etc.) remains the same.
    """

    def preference_ini(self, remote: RemoteVisionPC) -> Path:
        return remote.preference_ini

    def recipe_file(self, remote: RemoteVisionPC, info: RecipeInfo) -> Path:
        """
        Return a Path to Recipe.json inside the recipe-id directory.

        We try a few common RemoteVisionPC patterns first; if none exist,
        we fall back to "remote.recipe_file(...)" and replace the filename with Recipe.json.
        """
        recipe_id = info.recipe_id_3digit

        # Common pattern: remote.recipe_dir("001") -> Path
        for attr in ("recipe_dir", "recipe_folder", "recipe_id_dir"):
            fn = getattr(remote, attr, None)
            if callable(fn):
                base = fn(recipe_id)
                return Path(base) / "Recipe.json"

        # Common pattern: remote.recipe_root / "001" / "Recipe.json"
        for attr in ("recipe_root", "recipe_base", "recipe_base_dir", "recipes_root"):
            base = getattr(remote, attr, None)
            if base:
                return Path(base) / recipe_id / "Recipe.json"

        # Fallback: use existing recipe_file(...) but force name to Recipe.json
        try:
            p = remote.recipe_file(recipe_id, info.recipe_name)
            return p.with_name("Recipe.json")
        except Exception:
            # Absolute fallback (mainly for local testing)
            return Path(rf"C:\VisionPC\Recipe\{recipe_id}\Recipe.json")

    def kickout_xlsx(self, ctx: VisionContext, info: RecipeInfo) -> Path:
        # KickoutLists/Lead/<RecipeName>.xlsx
        return ctx.kickout_dir / f"{info.recipe_name}.xlsx"