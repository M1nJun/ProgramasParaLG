from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from preference_reader import RecipeInfo


@dataclass(frozen=True)
class RecipePaths:
    recipe_dir: Path
    recipe_file: Path


def locate_recipe_paths(info: RecipeInfo, visionpc_root: Path = Path(r"C:\VisionPC")) -> RecipePaths:
    """
    Uses:
      C:\\VisionPC\\Recipe\\{RecipeID_3digit}\\{RecipeName}

    Example:
      id=1 -> 001
      name=JF2
      => C:\\VisionPC\\Recipe\\001\\JF2
    """
    recipe_dir = visionpc_root / "Recipe" / info.recipe_id_3digit
    recipe_file = recipe_dir / info.recipe_name
    return RecipePaths(recipe_dir=recipe_dir, recipe_file=recipe_file)
