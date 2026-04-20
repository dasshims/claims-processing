from typing import Dict, List, Optional

import pandas as pd

from config import REQUIRED_STANDARD_FIELDS


def _get_source_column_for_target(mapping: Dict[str, Optional[str]], target_field: str) -> Optional[str]:
    for src, tgt in mapping.items():
        if tgt == target_field:
            return src
    return None


def validate_dataframe(df: pd.DataFrame, mapping: Dict[str, Optional[str]]) -> List[Dict]:
    errors: List[Dict] = []

    for required_field in REQUIRED_STANDARD_FIELDS:
        src_col = _get_source_column_for_target(mapping, required_field)
        if not src_col:
            errors.append(
                {
                    "row_index": None,
                    "source_column": None,
                    "target_field": required_field,
                    "error_type": "missing_required_field",
                    "message": f"No source column mapped to required field '{required_field}'.",
                }
            )
            continue

        series = df[src_col]

        null_rows = series[series.isna()].index.tolist()
        for i in null_rows[:100]:
            errors.append(
                {
                    "row_index": int(i),
                    "source_column": src_col,
                    "target_field": required_field,
                    "error_type": "null_value",
                    "message": f"Null value found for '{required_field}' in '{src_col}'.",
                }
            )

        if required_field == "date_of_service":
            parsed = pd.to_datetime(series, errors="coerce")
            invalid = parsed[~series.isna() & parsed.isna()].index.tolist()
            for i in invalid[:100]:
                errors.append(
                    {
                        "row_index": int(i),
                        "source_column": src_col,
                        "target_field": required_field,
                        "error_type": "invalid_date",
                        "message": f"Invalid date format in '{src_col}' for date_of_service.",
                    }
                )

        if required_field == "claim_amount":
            numeric = pd.to_numeric(series, errors="coerce")
            invalid = numeric[~series.isna() & numeric.isna()].index.tolist()
            for i in invalid[:100]:
                errors.append(
                    {
                        "row_index": int(i),
                        "source_column": src_col,
                        "target_field": required_field,
                        "error_type": "invalid_number",
                        "message": f"Invalid numeric value in '{src_col}' for claim_amount.",
                    }
                )

    return errors
