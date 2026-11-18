import json
from pathlib import Path

import pandas as pd


SEX_CODES = {
    "Male": "MLE",
    "Female": "FMLE",
    "Both sexes": "BTSX",
    "MLE": "MLE",
    "FMLE": "FMLE",
    "BTSX": "BTSX",
    "SEX_MLE": "MLE",
    "SEX_FMLE": "FMLE",
    "SEX_BTSX": "BTSX",
}
NORMALIZED_COLUMNS = [
    "country_iso3",
    "indicator_code",
    "year",
    "sex",
    "value",
]


def transform_who(raw_file: str | Path) -> pd.DataFrame:
    """Transform a saved WHO OData JSON file into normalized observations."""
    path = Path(raw_file)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict) or not isinstance(payload.get("value"), list):
        raise ValueError("Invalid WHO JSON: expected an object with a 'value' list")

    rows = []
    for item in payload["value"]:
        if not isinstance(item, dict):
            continue

        dim1_type = str(item.get("Dim1Type") or "").strip().lower()
        if dim1_type and dim1_type not in {"sex", "gender"}:
            continue

        sex = "BTSX"
        if dim1_type in {"sex", "gender"}:
            dimension_value = str(item.get("Dim1") or "").strip()
            sex = SEX_CODES.get(
                dimension_value,
                SEX_CODES.get(dimension_value.upper(), "BTSX"),
            )

        country_iso3 = item.get("SpatialDim")
        year = item.get("TimeDim")
        value = item.get("NumericValue")
        indicator_code = item.get("IndicatorCode")
        if not indicator_code:
            indicator_code = path.stem

        rows.append({
            "country_iso3": country_iso3,
            "indicator_code": indicator_code,
            "year": year,
            "sex": sex,
            "value": value,
        })

    return pd.DataFrame(rows, columns=NORMALIZED_COLUMNS)

