from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
from collections import defaultdict

from normalize import normalize_measure_name
from recipe_parser import MeasureOccurrence
from kickout_loader import KickoutList


@dataclass(frozen=True)
class MeasureRow:
    normalized_key: str
    display_name: str
    group: str             # "Upper"/"Lower"/"Both" (welding) OR "Anode"/"Cathode"/"Shared" (lead)
    expected_count: int
    found_count: int
    occurrences: List[MeasureOccurrence]
    bypassed_occurrences: List[MeasureOccurrence]

    @property
    def has_bypassed(self) -> bool:
        return len(self.bypassed_occurrences) > 0

    @property
    def is_missing(self) -> bool:
        return self.found_count < self.expected_count

    @property
    def is_pass(self) -> bool:
        return (not self.is_missing) and (not self.has_bypassed)


@dataclass(frozen=True)
class CheckReport:
    recipe_name: str
    recipe_id_3digit: str
    kickout_filename: str
    schema: str  # "welding" or "lead"

    required_counts: Dict[str, int]  # e.g. {"Upper": 30, "Lower": 27, "Both": 15} or {"Anode":..., ...}
    rows: List[MeasureRow]

    master_duplicates: Dict[str, List[str]]  # group -> duplicated normalized keys within that column
    config_warnings: List[str]               # non-fatal warnings (if any)


def _group_label_welding(in_upper: bool, in_lower: bool) -> str:
    if in_upper and in_lower:
        return "Both"
    if in_upper:
        return "Upper"
    return "Lower"


def _validate_no_overlap_for_lead(group_membership: Dict[str, List[str]]) -> None:
    # group_membership: normalized_key -> list of groups it's in
    overlaps = {k: gs for k, gs in group_membership.items() if len(gs) > 1}
    if overlaps:
        # You said this won't happen; if it does, it's a master-list config error.
        examples = []
        for k, gs in list(overlaps.items())[:10]:
            examples.append(f"{k} in {gs}")
        msg = (
            "Lead kickout list has overlaps across Anode/Cathode/Shared (not allowed). "
            f"Examples: {', '.join(examples)}"
        )
        raise ValueError(msg)


def check_kickout(
    measures: List[MeasureOccurrence],
    kickout: KickoutList,
    recipe_name: str,
    recipe_id_3digit: str,
    kickout_filename: str,
) -> CheckReport:
    """
    Shared engine for:
    - Welding: groups Upper/Lower, overlaps allowed => expected_count can be 2
    - Lead: groups Anode/Cathode/Shared, overlaps NOT allowed => expected_count always 1
    """
    by_norm: Dict[str, List[MeasureOccurrence]] = defaultdict(list)
    for occ in measures:
        key = normalize_measure_name(occ.name)
        if key:
            by_norm[key].append(occ)

    schema = (kickout.schema or "").lower().strip()
    config_warnings: List[str] = []

    # 1) Build membership: normalized_key -> groups it's required in
    group_membership: Dict[str, List[str]] = defaultdict(list)
    # also store display names per group, as-is from master list
    display_per_group: Dict[Tuple[str, str], str] = {}

    for group, mapping in kickout.groups.items():
        for norm_key, display in mapping.items():
            group_membership[norm_key].append(group)
            display_per_group[(group, norm_key)] = display

    # Lead: overlaps are a config error (you assured they won't happen)
    if schema == "lead":
        _validate_no_overlap_for_lead(group_membership)

    # 2) Required counts (for UI summary)
    required_counts: Dict[str, int] = {}
    for group, mapping in kickout.groups.items():
        required_counts[group] = len(mapping)

    # Welding: add "Both" count as convenience (if overlap exists)
    both_count = 0
    if schema == "welding":
        for k, gs in group_membership.items():
            if "Upper" in gs and "Lower" in gs:
                both_count += 1
        required_counts["Both"] = both_count

    # 3) Generate rows
    rows: List[MeasureRow] = []

    for norm_key in sorted(group_membership.keys()):
        groups = group_membership[norm_key]

        # Determine label and expected count
        if schema == "welding":
            in_upper = "Upper" in groups
            in_lower = "Lower" in groups
            expected = (1 if in_upper else 0) + (1 if in_lower else 0)
            group_label = _group_label_welding(in_upper, in_lower)

            # Choose display name:
            # - if in both and names differ, show "u / l"
            u = display_per_group.get(("Upper", norm_key))
            l = display_per_group.get(("Lower", norm_key))
            if u and l:
                display_name = u if u == l else f"{u} / {l}"
            else:
                display_name = u or l or norm_key

        else:
            # Lead: exactly one group
            group_label = groups[0]
            expected = 1
            display_name = display_per_group.get((group_label, norm_key), norm_key)

        occs = by_norm.get(norm_key, [])
        bypassed = [o for o in occs if o.bypass]

        rows.append(
            MeasureRow(
                normalized_key=norm_key,
                display_name=display_name,
                group=group_label,
                expected_count=expected,
                found_count=len(occs),
                occurrences=occs,
                bypassed_occurrences=bypassed,
            )
        )

    return CheckReport(
        recipe_name=recipe_name,
        recipe_id_3digit=recipe_id_3digit,
        kickout_filename=kickout_filename,
        schema=schema,
        required_counts=required_counts,
        rows=rows,
        master_duplicates=kickout.duplicates,
        config_warnings=config_warnings,
    )
