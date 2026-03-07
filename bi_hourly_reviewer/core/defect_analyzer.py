"""
Defect side analysis.

Responsibilities:
    - Given a defect row and its JUDGE-DEFECT value, determine which side
      (upper, lower, or both) the defect was detected on.
    - Handle both column naming conventions:
        Case 1: LOWER_<defect>-OK/NG / UPPER_<defect>-OK/NG
        Case 2: LOWER_<defect>-JUDGE / UPPER_<defect>-JUDGE

Does NOT read CSVs or filter rows — only analyzes a single row.
"""

from typing import Dict, List, Tuple

from config import (
    COL_JUDGE_DEFECT,
    SIDE_COLUMN_SUFFIXES,
    SIDE_NG_VALUES,
)


# Side constants
SIDE_UPPER = "UPPER"
SIDE_LOWER = "LOWER"
SIDE_BOTH = "BOTH"
SIDE_UNKNOWN = "UNKNOWN"


def determine_defect_side(row: Dict[str, str], headers: List[str] = None) -> str:
    """
    Determine which side the defect was caught on.

    Args:
        row: A single CSV row dict.
        headers: Optional list of all column headers (for column lookup).
                 If None, uses row keys.

    Returns:
        One of: "UPPER", "LOWER", "BOTH", "UNKNOWN".
    """
    defect_type = row.get(COL_JUDGE_DEFECT, "").strip()
    if not defect_type:
        return SIDE_UNKNOWN

    available_cols = headers if headers else list(row.keys())

    upper_ng = _check_side_ng(row, SIDE_UPPER, defect_type, available_cols)
    lower_ng = _check_side_ng(row, SIDE_LOWER, defect_type, available_cols)

    if upper_ng and lower_ng:
        return SIDE_BOTH
    elif upper_ng:
        return SIDE_UPPER
    elif lower_ng:
        return SIDE_LOWER
    else:
        return SIDE_UNKNOWN


def _check_side_ng(
    row: Dict[str, str],
    side: str,
    defect_type: str,
    available_cols: List[str],
) -> bool:
    """
    Check if a specific side has an NG value for the given defect type.

    Tries both naming conventions:
        {side}_{defect_type}-OK/NG
        {side}_{defect_type}-JUDGE

    Args:
        row: Row dict.
        side: "UPPER" or "LOWER".
        defect_type: Value from JUDGE-DEFECT column (e.g. "Tab_Damage", "B_R").
        available_cols: All column headers.

    Returns:
        True if this side has an NG/BYPASS_NG value.
    """
    for suffix in SIDE_COLUMN_SUFFIXES:
        col_name = f"{side}_{defect_type}{suffix}"
        if col_name in available_cols:
            value = row.get(col_name, "").strip()
            if value in SIDE_NG_VALUES:
                return True
    return False


def get_side_column_name(
    side: str,
    defect_type: str,
    available_cols: List[str],
) -> str:
    """
    Find the actual column name used for a given side and defect type.
    Useful for logging/debugging.

    Returns:
        The column name if found, or None.
    """
    for suffix in SIDE_COLUMN_SUFFIXES:
        col_name = f"{side}_{defect_type}{suffix}"
        if col_name in available_cols:
            return col_name
    return None


def build_defect_record(row: Dict[str, str]) -> Dict:
    """
    Build a structured defect record from a raw CSV row.
    Centralizes all the field extraction in one place.

    Returns:
        Dict with keys: no, date, time, model_id, lot_id, cell_id,
                        judge, judge_defect, side
    """
    from config import COL_NO, COL_DATE, COL_TIME, COL_MODEL_ID, COL_LOT_ID, COL_CELL_ID, COL_JUDGE
    from core.defect_filter import parse_date, parse_time

    return {
        "no": row.get(COL_NO, "").strip(),
        "date": parse_date(row),
        "time": parse_time(row),
        "model_id": row.get(COL_MODEL_ID, "").strip(),
        "lot_id": row.get(COL_LOT_ID, "").strip(),
        "cell_id": row.get(COL_CELL_ID, "").strip(),
        "judge": row.get(COL_JUDGE, "").strip(),
        "judge_defect": row.get(COL_JUDGE_DEFECT, "").strip(),
        "side": determine_defect_side(row),
        "_raw_row": row,
    }