# recipe_parser.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import xml.etree.ElementTree as ET

from vision.lead.recipe_json_parser import parse_lead_recipe_json_file


@dataclass(frozen=True)
class MeasureOccurrence:
    item_tag: str          # e.g. "MeasureItem_50" or "JSON[12]"
    index: Optional[int]   # parsed index if available, else None
    name: str              # original name
    bypass: bool           # bypass flag


class RecipeParseError(Exception):
    pass


# -------------------------
# Welding XML parser
# -------------------------

def _parse_measure_item_index(tag: str) -> Optional[int]:
    # Expected: "MeasureItem_0", "MeasureItem_1", ...
    if not tag.startswith("MeasureItem_"):
        return None
    try:
        return int(tag.split("_", 1)[1])
    except Exception:
        return None


def _parse_welding_recipe_xml(recipe_file: Path) -> List[MeasureOccurrence]:
    """
    Parses recipe XML:
      <MeasureList>
        <MeasureItem_0>
          <Name>...</Name>
          <Bypass>true/false</Bypass>
        </MeasureItem_0>
        ...
      </MeasureList>
    """
    if not recipe_file.exists():
        raise RecipeParseError(f"Recipe file not found: {recipe_file}")

    try:
        tree = ET.parse(recipe_file)
        root = tree.getroot()
    except ET.ParseError as e:
        raise RecipeParseError(f"XML parse error in {recipe_file}: {e}")

    measure_list = root.find("MeasureList")
    if measure_list is None:
        raise RecipeParseError("Missing <MeasureList> section in recipe file")

    out: List[MeasureOccurrence] = []

    for child in list(measure_list):
        name_el = child.find("Name")
        bypass_el = child.find("Bypass")

        if name_el is None or bypass_el is None:
            continue

        name = (name_el.text or "").strip()
        bypass_text = (bypass_el.text or "").strip().lower()

        if bypass_text not in ("true", "false"):
            raise RecipeParseError(
                f"Invalid <Bypass> value {bypass_el.text!r} in {child.tag}"
            )

        out.append(
            MeasureOccurrence(
                item_tag=child.tag,
                index=_parse_measure_item_index(child.tag),
                name=name,
                bypass=(bypass_text == "true"),
            )
        )

    return out


# -------------------------
# Lead JSON parser adapter
# -------------------------

def _parse_lead_recipe_json(recipe_file: Path) -> List[MeasureOccurrence]:
    """
    Parses Lead Recipe.json and converts to MeasureOccurrence list.
    """
    lead_items = parse_lead_recipe_json_file(recipe_file)

    out: List[MeasureOccurrence] = []
    for i, m in enumerate(lead_items):
        out.append(
            MeasureOccurrence(
                item_tag=f"JSON[{i}]",
                index=i,
                name=m.name,
                bypass=bool(m.bypass),
            )
        )
    return out


# -------------------------
# Public API (auto-detect)
# -------------------------

def parse_recipe_measures(recipe_file: Path) -> List[MeasureOccurrence]:
    """
    Auto-detect by extension:
      - .xml => Welding parsing
      - .json => Lead parsing
    """
    suf = recipe_file.suffix.lower()

    if suf == ".xml":
        return _parse_welding_recipe_xml(recipe_file)

    if suf == ".json":
        return _parse_lead_recipe_json(recipe_file)

    # If suffix is unknown, try:
    # - if file name looks like Recipe.json, treat as json
    # - otherwise default to xml (historic behavior)
    if recipe_file.name.lower() == "recipe.json":
        return _parse_lead_recipe_json(recipe_file)

    return _parse_welding_recipe_xml(recipe_file)