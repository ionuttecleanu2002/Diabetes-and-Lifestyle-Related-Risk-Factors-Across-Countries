import json
from pathlib import Path
from typing import Iterable

import pandas as pd


NORMALIZED_COLUMNS = [
    "country_iso3",
    "indicator_code",
    "year",
    "sex",
    "value",
]


def load_worldbank_country_codes(
    countries_file: str | Path | None,
) -> set[str] | None:
    """Load valid country ISO3 codes from a saved World Bank countries response."""
    if countries_file is None:
        return None

    path = Path(countries_file)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, list) or len(payload) != 2:
        raise ValueError("Invalid World Bank countries JSON")
    rows = payload[1]
    if not isinstance(rows, list):
        raise ValueError("Invalid World Bank countries JSON")

    codes = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        iso3 = str(row.get("id") or "").strip().upper()
        region = row.get("region")
        aggregate_region = (
            isinstance(region, dict)
            and str(region.get("id") or "").upper() in {"", "NA"}
        )
        if len(iso3) == 3:
            if not aggregate_region:
                codes.add(iso3)
    return codes


def transform_worldbank(
    raw_file: str | Path,
    countries_file: str | Path | None = None,
) -> pd.DataFrame:
    """Transform a saved World Bank indicator JSON file."""
    path = Path(raw_file)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, list) or len(payload) != 2:
        raise ValueError(
            "Invalid World Bank JSON: expected [metadata, observations]"
        )
    observations = payload[1]
    if not isinstance(observations, list):
        raise ValueError("Invalid World Bank JSON: observations must be a list")

    valid_countries = load_worldbank_country_codes(countries_file)
    rows = []
    for item in observations:
        if not isinstance(item, dict):
            continue

        country_iso3 = str(item.get("countryiso3code") or "").strip().upper()
        indicator_code = (
            str((item.get("indicator") or {}).get("id") or "").strip().upper()
            if isinstance(item.get("indicator"), dict)
            else ""
        )
        if not indicator_code:
            indicator_code = path.stem
        if not country_iso3 or len(country_iso3) != 3:
            continue
        if valid_countries is not None and country_iso3 not in valid_countries:
            continue

        rows.append({
            "country_iso3": country_iso3,
            "indicator_code": indicator_code,
            "year": item.get("date"),
            "sex": "BTSX",
            "value": item.get("value"),
        })

    return pd.DataFrame(rows, columns=NORMALIZED_COLUMNS)

