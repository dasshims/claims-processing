from typing import Dict, List

import pandas as pd

from config import REQUIRED_STANDARD_FIELDS

FIELD_HINTS = {
    "member_id": ["member", "mem", "mbr"],
    "claim_id": ["claim", "clm"],
    "claim_amount": ["amount", "amt", "billed"],
    "date_of_service": ["date", "dos", "service"],
    "provider_id": ["provider", "prov", "doctor"],
}


def assess_readiness(df: pd.DataFrame) -> Dict:
    columns = [str(c).lower() for c in df.columns]
    blockers: List[Dict] = []
    score = 100

    for required_field in REQUIRED_STANDARD_FIELDS:
        hints = FIELD_HINTS.get(required_field, [])
        has_candidate = any(any(h in col for h in hints) for col in columns)
        if not has_candidate:
            blockers.append(
                {
                    "code": f"missing_candidate_{required_field}",
                    "message": f"No likely source column found for {required_field}.",
                    "severity": "high",
                }
            )
            score -= 18

    if len(df) < 5:
        blockers.append(
            {
                "code": "low_row_count",
                "message": "Very small sample size may reduce mapping confidence.",
                "severity": "medium",
            }
        )
        score -= 10

    null_ratio = float(df.isna().mean().mean()) if not df.empty else 1.0
    if null_ratio > 0.2:
        blockers.append(
            {
                "code": "high_null_ratio",
                "message": f"Dataset has high null ratio ({null_ratio:.1%}).",
                "severity": "medium",
            }
        )
        score -= 12

    score = max(0, min(100, score))

    if score >= 80:
        status = "ready"
    elif score >= 55:
        status = "at_risk"
    else:
        status = "blocked"

    summary = {
        "ready": "Dataset is mostly ready for automated mapping and validation.",
        "at_risk": "Dataset is usable, but some gaps may require manual decisions.",
        "blocked": "Dataset is likely to fail onboarding without source data corrections.",
    }[status]

    return {
        "score": score,
        "status": status,
        "blockers": blockers,
        "summary": summary,
    }
