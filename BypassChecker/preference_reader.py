# preference_reader.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import configparser


# -----------------------------
# Data model
# -----------------------------

@dataclass(frozen=True)
class RecipeInfo:
    recipe_id_3digit: str   # "001"
    recipe_name: str        # "JF2"


# -----------------------------
# Encoding utilities
# -----------------------------

def _detect_text_encoding(raw: bytes) -> str:
    """
    Preference.ini in your environment is commonly UTF-16 LE (BOM: FF FE).
    This helper detects BOM and returns a reasonable encoding.
    """
    if raw.startswith(b"\xff\xfe"):
        return "utf-16"      # Python will handle LE/BE based on BOM
    if raw.startswith(b"\xfe\xff"):
        return "utf-16"
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    return "utf-8"           # fallback (we still retry with cp1252 below)


def _read_text_with_fallbacks(path: Path) -> str:
    raw = path.read_bytes()
    enc = _detect_text_encoding(raw)

    # 1) try detected encoding
    try:
        return raw.decode(enc)
    except Exception:
        pass

    # 2) try common fallbacks
    for fallback in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return raw.decode(fallback)
        except Exception:
            continue

    # last resort (never crash)
    return raw.decode("latin-1", errors="replace")


# -----------------------------
# INI parsing
# -----------------------------

def _parse_ini(path: Path) -> configparser.ConfigParser:
    text = _read_text_with_fallbacks(path)

    cfg = configparser.ConfigParser()
    # preserve case if you want; your keys look like LastRecipeID etc
    cfg.optionxform = str  # do NOT lowercase keys
    cfg.read_string(text)
    return cfg


def _get_recipe_fields(cfg: configparser.ConfigParser, vision_mode: str) -> Tuple[str, str]:
    """
    Welding Preference.ini:
      [Recipe]
      LastRecipeID   = 1
      LastRecipeName = JF2

    Lead Preference.ini:
      [Recipe]
      LastRecipeID  = JF2
      LastRecipeNum = 1

    Returns: (recipe_num_str, recipe_name_str)
    """
    if not cfg.has_section("Recipe"):
        raise ValueError("Missing [Recipe] section in Preference.ini")

    mode = (vision_mode or "").strip().lower()

    if mode == "lead":
        # Lead: folder number is in LastRecipeNum, name in LastRecipeID
        recipe_num = cfg.get("Recipe", "LastRecipeNum", fallback="").strip()
        recipe_name = cfg.get("Recipe", "LastRecipeID", fallback="").strip()
    else:
        # Welding (default): folder number in LastRecipeID, name in LastRecipeName
        recipe_num = cfg.get("Recipe", "LastRecipeID", fallback="").strip()
        recipe_name = cfg.get("Recipe", "LastRecipeName", fallback="").strip()

    if not recipe_num:
        raise ValueError(f"Missing recipe number for vision_mode={vision_mode!r}")
    if not recipe_name:
        raise ValueError(f"Missing recipe name for vision_mode={vision_mode!r}")

    return recipe_num, recipe_name


def _to_3digit_folder(recipe_num: str) -> str:
    """
    Accepts '1', '001', ' 1 ' -> returns '001'
    """
    s = recipe_num.strip()
    try:
        n = int(s)
    except Exception:
        # If it's already something weird, try to keep it stable but still 3-digit if possible
        # (If it’s truly non-numeric, let upstream handle it as invalid)
        raise ValueError(f"Recipe number is not numeric: {recipe_num!r}")

    return f"{n:03d}"


# -----------------------------
# Public API used by pipeline
# -----------------------------

def read_recipe_info(preference_ini_path: Path, vision_mode: str = "Welding") -> RecipeInfo:
    """
    Reads Preference.ini and returns the active recipe folder + recipe name.

    vision_mode is required to pick the correct keys for Lead vs Welding.
    Default keeps older call sites working.
    """
    cfg = _parse_ini(Path(preference_ini_path))
    recipe_num, recipe_name = _get_recipe_fields(cfg, vision_mode=vision_mode)
    folder_3digit = _to_3digit_folder(recipe_num)

    return RecipeInfo(recipe_id_3digit=folder_3digit, recipe_name=recipe_name)