from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
import math
from typing import Any

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import Country, ImportLog, Indicator, Observation, Source


OBSERVATION_CONSTRAINT = "uq_observation_country_indicator_year_sex_age"
REQUIRED_COLUMNS = {
    "country_iso3",
    "indicator_code",
    "year",
    "sex",
    "value",
}


def _chunks(rows: Sequence[dict[str, Any]], chunk_size: int):
    for start in range(0, len(rows), chunk_size):
        yield rows[start : start + chunk_size]


def _records_from_frame(frame: pd.DataFrame) -> list[dict[str, Any]]:
    missing_columns = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing_columns:
        raise ValueError(
            "Missing required observation columns: " + ", ".join(missing_columns)
        )

    working = frame.copy()
    if "age_group" not in working:
        working["age_group"] = "All ages"
    if "is_outlier" not in working:
        working["is_outlier"] = False

    for column in ("country_iso3", "indicator_code", "sex"):
        working[column] = working[column].astype("string").str.strip()
    working["country_iso3"] = working["country_iso3"].str.upper()
    working["sex"] = working["sex"].str.upper()
    working["age_group"] = working["age_group"].fillna("All ages").astype("string").str.strip()
    working.loc[working["age_group"].eq(""), "age_group"] = "All ages"
    working = working.drop_duplicates(
        subset=["country_iso3", "indicator_code", "year", "sex", "age_group"],
        keep="last",
    )
    records: list[dict[str, Any]] = []
    for row in working.to_dict(orient="records"):
        country_iso3 = str(row["country_iso3"]).strip().upper()
        indicator_code = str(row["indicator_code"]).strip()
        sex = str(row["sex"]).strip().upper()
        year_value = pd.to_numeric(row["year"], errors="coerce")
        value = pd.to_numeric(row["value"], errors="coerce")

        if len(country_iso3) != 3 or not indicator_code:
            raise ValueError("Observation has an invalid country or indicator code")
        if pd.isna(year_value) or not float(year_value).is_integer():
            raise ValueError(f"Observation has an invalid year: {row['year']!r}")
        if pd.isna(value) or not math.isfinite(float(value)):
            raise ValueError(f"Observation has an invalid value: {row['value']!r}")
        if sex not in {"BTSX", "MLE", "FMLE"}:
            raise ValueError(f"Observation has an invalid sex code: {sex!r}")

        age_group = row["age_group"]
        if pd.isna(age_group) or not str(age_group).strip():
            age_group = "All ages"
        is_outlier = row["is_outlier"]
        if pd.isna(is_outlier):
            is_outlier = False
        records.append({
            "country_iso3": country_iso3,
            "indicator_code": indicator_code,
            "year": int(year_value),
            "sex": sex,
            "age_group": str(age_group).strip(),
            "value": float(value),
            "is_outlier": bool(is_outlier),
        })
    return records


def _country_records(countries: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized = {}
    for country in countries:
        code = str(country.get("country_iso3") or "").strip().upper()
        name = str(country.get("country_name") or "").strip()
        if len(code) != 3 or not name:
            raise ValueError("Country records require ISO3 code and country name")
        normalized[code] = {
            "country_iso3": code,
            "country_name": name[:100],
            "region": country.get("region"),
        }
    return list(normalized.values())


def _observation_upsert(records: Sequence[dict[str, Any]]):
    insert_stmt = pg_insert(Observation).values(records)
    return insert_stmt.on_conflict_do_update(
        constraint=OBSERVATION_CONSTRAINT,
        set_={
            "value": insert_stmt.excluded.value,
            "is_outlier": insert_stmt.excluded.is_outlier,
            "imported_at": func.now(),
        },
    )


def load_observations(
    session: Session,
    frame: pd.DataFrame,
    *,
    source_name: str,
    source_url: str | None = None,
    source_description: str | None = None,
    countries: Iterable[Mapping[str, Any]] = (),
    indicator_metadata: Mapping[str, Mapping[str, Any]] | None = None,
    chunk_size: int = 1000,
) -> int:
    """Atomically upsert source metadata and observations.

    The caller must pass a fresh SQLAlchemy Session. Any database failure rolls
    the complete import back; successful imports receive one import_log row.
    """
    if not source_name or not source_name.strip():
        raise ValueError("source_name is required")
    if chunk_size < 1:
        raise ValueError("chunk_size must be greater than zero")

    records = _records_from_frame(frame)
    country_rows = _country_records(countries)
    country_codes = {item["country_iso3"] for item in country_rows}
    observation_countries = {item["country_iso3"] for item in records}
    indicator_codes = sorted({item["indicator_code"] for item in records})
    metadata = indicator_metadata or {}
    started_at = datetime.now(timezone.utc)

    with session.begin():
        source_insert = pg_insert(Source).values(
            source_name=source_name.strip(),
            source_url=source_url,
            description=source_description,
        )
        source_stmt = source_insert.on_conflict_do_update(
            index_elements=[Source.source_name],
            set_={
                "source_url": func.coalesce(
                    source_insert.excluded.source_url,
                    Source.source_url,
                ),
                "description": func.coalesce(
                    source_insert.excluded.description,
                    Source.description,
                ),
            },
        ).returning(Source.source_id)
        source_id = session.execute(source_stmt).scalar_one()

        for batch in _chunks(country_rows, chunk_size):
            country_insert = pg_insert(Country).values(batch)
            country_stmt = country_insert.on_conflict_do_update(
                index_elements=[Country.country_iso3],
                set_={
                    "country_name": country_insert.excluded.country_name,
                    "region": func.coalesce(
                        country_insert.excluded.region,
                        Country.region,
                    ),
                },
            )
            session.execute(country_stmt)

        missing_country_codes = observation_countries.difference(country_codes)
        if missing_country_codes:
            existing = set(
                session.scalars(
                    select(Country.country_iso3).where(
                        Country.country_iso3.in_(missing_country_codes)
                    )
                ).all()
            )
            missing_country_codes.difference_update(existing)
        if missing_country_codes:
            raise ValueError(
                "No country metadata exists for observation codes: "
                + ", ".join(sorted(missing_country_codes))
            )

        indicator_rows = []
        for code in indicator_codes:
            detail = metadata.get(code, {})
            indicator_rows.append({
                "indicator_code": code,
                "indicator_name": (
                    str(detail.get("indicator_name") or code).strip()[:255]
                ),
                "unit": detail.get("unit"),
                "description": detail.get("description"),
                "source_id": source_id,
            })

        indicator_ids: dict[str, int] = {}
        for batch in _chunks(indicator_rows, chunk_size):
            indicator_insert = pg_insert(Indicator).values(batch)
            indicator_stmt = indicator_insert.on_conflict_do_update(
                index_elements=[Indicator.indicator_code],
                set_={
                    "indicator_name": indicator_insert.excluded.indicator_name,
                    "unit": func.coalesce(
                        indicator_insert.excluded.unit,
                        Indicator.unit,
                    ),
                    "description": func.coalesce(
                        indicator_insert.excluded.description,
                        Indicator.description,
                    ),
                    "source_id": indicator_insert.excluded.source_id,
                },
            ).returning(Indicator.indicator_code, Indicator.indicator_id)
            for row in session.execute(indicator_stmt).mappings():
                indicator_ids[row["indicator_code"]] = row["indicator_id"]

        observation_rows = [
            {
                "country_iso3": item["country_iso3"],
                "indicator_id": indicator_ids[item["indicator_code"]],
                "year": item["year"],
                "sex": item["sex"],
                "age_group": item["age_group"],
                "value": item["value"],
                "is_outlier": item["is_outlier"],
            }
            for item in records
        ]
        for batch in _chunks(observation_rows, chunk_size):
            session.execute(_observation_upsert(batch))

        finished_at = datetime.now(timezone.utc)
        session.add(
            ImportLog(
                source_id=source_id,
                started_at=started_at,
                finished_at=finished_at,
                status="success",
                records_imported=len(observation_rows),
            )
        )

    return len(records)
