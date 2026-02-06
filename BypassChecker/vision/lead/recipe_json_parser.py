# vision/lead/recipe_json_parser.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import json


@dataclass(frozen=True)
class LeadMeasureItem:
    """
    Extracted measurement item from Lead Recipe.json
    """
    name: str
    bypass: bool
    json_path: str          # debugging / trace path in json
    order_index: int        # extraction order


class LeadRecipeJsonParseError(Exception):
    pass


def _is_measure_dict(d: Dict[str, Any]) -> bool:
    """
    Heuristic for "this dict is a measure row".
    We treat a dict as a measure if it has:
      - NAME (string-ish)
      - BY_PASS (bool-ish or 0/1)
    Optional:
      - MEASUREMENT true (many items have it)
    """
    if "NAME" not in d:
        return False
    if "BY_PASS" not in d:
        return False
    # Some JSONs may include NAME/BY_PASS for other sections; MEASUREMENT helps,
    # but don't require it to avoid missing valid measures.
    return True


def _coerce_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("true", "1", "yes", "y"):
            return True
        if s in ("false", "0", "no", "n", ""):
            return False
    return False


def _walk_json(obj: Any, path: str = "$") -> Iterable[Tuple[str, Any]]:
    """
    Depth-first walk over json structure yielding (path, node).
    """
    yield path, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_json(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_json(v, f"{path}[{i}]")


def extract_lead_measures(recipe_json: Any) -> List[LeadMeasureItem]:
    """
    Extract measures from an already-loaded JSON structure.
    Returns items in traversal order.
    """
    items: List[LeadMeasureItem] = []
    order = 0

    for p, node in _walk_json(recipe_json):
        if isinstance(node, dict) and _is_measure_dict(node):
            name = str(node.get("NAME", "")).strip()
            if not name:
                continue

            bypass = _coerce_bool(node.get("BY_PASS", False))

            # If MEASUREMENT exists and is explicitly false, skip it
            if "MEASUREMENT" in node and not _coerce_bool(node.get("MEASUREMENT")):
                continue

            items.append(
                LeadMeasureItem(
                    name=name,
                    bypass=bypass,
                    json_path=p,
                    order_index=order,
                )
            )
            order += 1

    return items


def parse_lead_recipe_json_file(path: Path) -> List[LeadMeasureItem]:
    if not path.exists():
        raise LeadRecipeJsonParseError(f"Recipe.json not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise LeadRecipeJsonParseError(f"Failed to load JSON {path}: {e}")

    items = extract_lead_measures(data)
    if not items:
        raise LeadRecipeJsonParseError(
            f"No measures found in {path}. "
            f"(Expected dicts containing NAME + BY_PASS; optionally MEASUREMENT=true)"
        )
    return items