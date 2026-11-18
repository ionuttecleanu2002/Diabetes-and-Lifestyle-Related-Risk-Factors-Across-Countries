import json
import logging
from pathlib import Path
from typing import Callable, Iterable

import pandas as pd

from etl.clean import clean_observations
from etl.extract_worldbank import (
    WORLD_BANK_BASE_URL,
    extract_worldbank,
    extract_worldbank_countries,
)
from etl.import_common import (
    NORMALIZED_COLUMNS,
    load_frame,
    log_cleaning_summary,
    worldbank_country_records,
)
from etl.transform_worldbank import transform_worldbank


logger = logging.getLogger(__name__)
WORLD_BANK_INDICATORS = (
    "SH.XPD.CHEX.GD.ZS",
    "SH.IMM.MEAS",
    "SP.DYN.IMRT.IN",
    "NY.GDP.PCAP.CD",
    "SH.STA.DIAB.ZS",
    "SH.PRV.SMOK",
)
SOURCE_NAME = "World Bank"


def _indicator_name(raw_file: Path, indicator_code: str) -> str:
    with raw_file.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list) and len(payload) == 2:
        for row in payload[1] or []:
            if isinstance(row, dict):
                indicator = row.get("indicator")
                if isinstance(indicator, dict) and indicator.get("value"):
                    return str(indicator["value"])
    return indicator_code


def import_worldbank(
    raw_dir: str | Path = "data/raw/worldbank",
    *,
    indicators: Iterable[str] = WORLD_BANK_INDICATORS,
    force: bool = False,
    load_function: Callable[..., int] | None = None,
) -> dict[str, dict[str, int | str]]:
    """Import cached World Bank data; fetch only files that are not cached."""
    directory = Path(raw_dir)
    directory.mkdir(parents=True, exist_ok=True)
    load = load_function or load_frame

    countries_file = directory / "countries.json"
    if not countries_file.exists() or force:
        countries_file, _ = extract_worldbank_countries(
            raw_dir=directory,
            force=force,
        )
    countries = worldbank_country_records(countries_file)
    country_codes = {item["country_iso3"] for item in countries}

    empty_frame = pd.DataFrame(columns=NORMALIZED_COLUMNS)
    load(
        empty_frame,
        source_name=SOURCE_NAME,
        source_url=WORLD_BANK_BASE_URL,
        source_description="World Bank Indicators API",
        countries=countries,
    )

    result: dict[str, dict[str, int | str]] = {
        "imported": {},
        "failures": {},
    }
    for indicator_code in indicators:
        try:
            raw_file = directory / f"{indicator_code}.json"
            if not raw_file.exists() or force:
                raw_file, _ = extract_worldbank(
                    indicator_code,
                    raw_dir=directory,
                    force=force,
                )
            frame = transform_worldbank(raw_file, countries_file)
            cleaned, removal_log = clean_observations(frame, country_codes)
            log_cleaning_summary(SOURCE_NAME, removal_log)
            count = load(
                cleaned,
                source_name=SOURCE_NAME,
                source_url=WORLD_BANK_BASE_URL,
                source_description="World Bank Indicators API",
                indicator_metadata={
                    indicator_code: {
                        "indicator_name": _indicator_name(raw_file, indicator_code)
                    }
                },
            )
            result["imported"][indicator_code] = count
            logger.info(
                "Imported %d observations for World Bank indicator %s",
                count,
                indicator_code,
            )
        except Exception as exc:
            logger.exception(
                "World Bank import failed for indicator %s",
                indicator_code,
            )
            result["failures"][indicator_code] = str(exc)
    return result


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    result = import_worldbank()
    if result["failures"]:
        raise RuntimeError(
            "Some World Bank indicators failed: "
            + ", ".join(sorted(result["failures"]))
        )


if __name__ == "__main__":
    main()
