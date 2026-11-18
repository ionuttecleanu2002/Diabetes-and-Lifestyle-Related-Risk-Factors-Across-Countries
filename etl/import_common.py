import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Country
from etl.load import load_observations


logger = logging.getLogger(__name__)
NORMALIZED_COLUMNS = [
    "country_iso3",
    "indicator_code",
    "year",
    "sex",
    "value",
]


def load_frame(frame: pd.DataFrame, **kwargs: Any) -> int:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured")
    with SessionLocal() as session:
        return load_observations(session, frame, **kwargs)


def valid_country_codes() -> set[str]:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured")
    with SessionLocal() as session:
        codes = set(session.scalars(select(Country.country_iso3)).all())
    if not codes:
        raise RuntimeError(
            "The country table is empty; run `python -m etl.import_worldbank` first"
        )
    return codes


def worldbank_country_records(raw_file: str | Path) -> list[dict[str, Any]]:
    path = Path(raw_file)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list) or len(payload) != 2:
        raise ValueError("Invalid World Bank countries response")
    rows = payload[1]
    if not isinstance(rows, list):
        raise ValueError("Invalid World Bank countries response")

    countries = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        code = str(row.get("id") or "").strip().upper()
        name = str(row.get("name") or "").strip()
        region = row.get("region")
        if (
            len(code) != 3
            or not name
            or not isinstance(region, dict)
            or str(region.get("id") or "").upper() in {"", "NA"}
        ):
            continue
        countries.append({
            "country_iso3": code,
            "country_name": name,
            "region": region.get("value"),
        })
    if not countries:
        raise ValueError("World Bank countries response contains no valid countries")
    return countries


def log_cleaning_summary(source_name: str, removed_rows: list[str]) -> None:
    for entry in removed_rows:
        logger.info("%s cleaning: %s", source_name, entry)
