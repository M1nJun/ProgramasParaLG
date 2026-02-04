from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


@dataclass(frozen=True)
class RecipeInfo:
    recipe_id_int: int
    recipe_id_3digit: str
    recipe_name: str


class PreferenceReadError(Exception):
    pass


def _parse_ini_lines_for_recipe(lines: list[str]) -> Tuple[Optional[int], Optional[str]]:
    in_recipe = False
    last_id: Optional[int] = None
    last_name: Optional[str] = None

    for raw in lines:
        line = raw.strip()

        if not line:
            continue

        # section headers
        if line.startswith("[") and line.endswith("]"):
            in_recipe = (line.lower() == "[recipe]")
            continue

        if not in_recipe:
            continue

        # key = value
        if "=" not in line:
            continue

        key, val = [x.strip() for x in line.split("=", 1)]
        key_l = key.lower()

        if key_l == "lastrecipeid":
            try:
                last_id = int(val)
            except ValueError:
                raise PreferenceReadError(f"Invalid LastRecipeID value: {val!r}")

        elif key_l == "lastrecipename":
            # recipe file has no extension per your system
            last_name = val

        # early exit if both found
        if last_id is not None and last_name:
            return last_id, last_name

    return last_id, last_name


def read_recipe_info(preference_ini_path: Path) -> RecipeInfo:
    """
    Reads Preference.ini (UTF-16 in your environment) and extracts:
      [Recipe]
      LastRecipeID = 1
      LastRecipeName = JF2
    """
    if not preference_ini_path.exists():
        raise PreferenceReadError(f"Preference.ini not found: {preference_ini_path}")

    # Your uploaded Preference.ini is UTF-16, so we default to that.
    # If a PC ever uses UTF-8, we can add fallback later.
    try:
        text = preference_ini_path.read_text(encoding="utf-16")
    except UnicodeError as e:
        raise PreferenceReadError(
            f"Failed to decode {preference_ini_path} as UTF-16. Error: {e}"
        )

    lines = text.splitlines()
    rid, rname = _parse_ini_lines_for_recipe(lines)

    if rid is None:
        raise PreferenceReadError("Missing [Recipe] LastRecipeID in Preference.ini")
    if not rname:
        raise PreferenceReadError("Missing [Recipe] LastRecipeName in Preference.ini")

    rid3 = f"{rid:03d}"
    return RecipeInfo(recipe_id_int=rid, recipe_id_3digit=rid3, recipe_name=rname)
