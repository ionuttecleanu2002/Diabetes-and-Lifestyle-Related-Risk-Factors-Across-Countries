import csv
from pathlib import Path

import pandas as pd


NORMALIZED_COLUMNS = [
    "country_iso3",
    "indicator_code",
    "year",
    "sex",
    "value",
]

AGGREGATE_ISO3_CODES = {
    "WLD",
    "OWID_WRL",
}


def transform_owid(
    raw_file: str | Path,
    indicator_code: str | None = None,
    valid_country_codes: set[str] | None = None,
) -> pd.DataFrame:
    """Transform a saved OWID chart CSV into normalized observations."""
    path = Path(raw_file)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        required = {"Entity", "Code", "Year"}
        missing = sorted(required.difference(fieldnames))
        if missing:
            raise ValueError(
                "Invalid OWID CSV: missing required columns: "
                + ", ".join(missing)
            )

        value_columns = [
            name for name in fieldnames
            if name not in {"Entity", "Code", "Year"}
        ]
        if len(value_columns) != 1:
            raise ValueError(
                "Invalid OWID CSV: expected exactly one value column"
            )
        value_column = value_columns[0]
        code = indicator_code or value_column or path.stem

        rows = []
        for item in reader:
            country_iso3 = str(item.get("Code") or "").strip().upper()
            if len(country_iso3) != 3:
                continue
            if country_iso3 in AGGREGATE_ISO3_CODES:
                continue
            if valid_country_codes is not None and country_iso3 not in valid_country_codes:
                continue
            rows.append({
                "country_iso3": country_iso3,
                "indicator_code": code,
                "year": item.get("Year"),
                "sex": "BTSX",
                "value": item.get(value_column),
            })

    return pd.DataFrame(rows, columns=NORMALIZED_COLUMNS)
