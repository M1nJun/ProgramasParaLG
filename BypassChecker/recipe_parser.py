from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class MeasureOccurrence:
    item_tag: str          # e.g. "MeasureItem_50"
    index: Optional[int]   # parsed index if available, else None
    name: str              # original <Name> text
    bypass: bool           # parsed <Bypass>


class RecipeParseError(Exception):
    pass


def _parse_measure_item_index(tag: str) -> Optional[int]:
    # Expected: "MeasureItem_0", "MeasureItem_1", ...
    if not tag.startswith("MeasureItem_"):
        return None
    try:
        return int(tag.split("_", 1)[1])
    except Exception:
        return None


def parse_recipe_measures(recipe_file: Path) -> List[MeasureOccurrence]:
    """
    Parses recipe XML:
      <MeasureList>
        <MeasureItem_0>
          <Name>...</Name>
          <Bypass>true/false</Bypass>
        </MeasureItem_0>
        ...
      </MeasureList>

    Returns a list of occurrences (order preserved).
    """
    if not recipe_file.exists():
        raise RecipeParseError(f"Recipe file not found: {recipe_file}")

    try:
        # Your sample recipe files are UTF-8 XML and parse cleanly.
        tree = ET.parse(recipe_file)
        root = tree.getroot()
    except ET.ParseError as e:
        raise RecipeParseError(f"XML parse error in {recipe_file}: {e}")

    measure_list = root.find("MeasureList")
    if measure_list is None:
        raise RecipeParseError("Missing <MeasureList> section in recipe file")

    out: List[MeasureOccurrence] = []

    for child in list(measure_list):
        # child.tag example: "MeasureItem_0"
        name_el = child.find("Name")
        bypass_el = child.find("Bypass")

        if name_el is None or bypass_el is None:
            # Skip malformed items; we can tighten this later if needed
            continue

        name = (name_el.text or "").strip()
        bypass_text = (bypass_el.text or "").strip().lower()

        if bypass_text not in ("true", "false"):
            raise RecipeParseError(
                f"Invalid <Bypass> value {bypass_el.text!r} in {child.tag}"
            )

        bypass = (bypass_text == "true")

        out.append(
            MeasureOccurrence(
                item_tag=child.tag,
                index=_parse_measure_item_index(child.tag),
                name=name,
                bypass=bypass,
            )
        )

    return out
