import json
import logging
from pathlib import Path
from typing import Callable

from etl.clean import clean_observations
from etl.extract_who import WHO_BASE_URL, extract_who
from etl.import_common import load_frame, log_cleaning_summary, valid_country_codes
from etl.transform_who import transform_who


logger = logging.getLogger(__name__)
WHO_INDICATOR = "WHOSIS_000001"
SOURCE_NAME = "WHO GHO"


def _indicator_name(raw_file: Path) -> str:
    with raw_file.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict) and isinstance(payload.get("value"), list):
        for row in payload["value"]:
            if isinstance(row, dict) and row.get("IndicatorName"):
                return str(row["IndicatorName"])
    return WHO_INDICATOR


def import_who(
    raw_dir: str | Path = "data/raw/who",
    *,
    indicator_code: str = WHO_INDICATOR,
    force: bool = False,
    load_function: Callable[..., int] | None = None,
    country_codes: set[str] | None = None,
) -> int:
    """Transform and load a cached WHO indicator, fetching only if absent."""
    directory = Path(raw_dir)
    directory.mkdir(parents=True, exist_ok=True)
    load = load_function or load_frame
    raw_file = directory / f"{indicator_code}.json"
    if not raw_file.exists() or force:
        raw_file, _ = extract_who(
            indicator_code,
            country_codes=country_codes,
            raw_dir=directory,
            force=force,
        )

    valid_codes = country_codes if country_codes is not None else valid_country_codes()
    frame = transform_who(raw_file)
    cleaned, removal_log = clean_observations(frame, valid_codes)
    log_cleaning_summary(SOURCE_NAME, removal_log)
    count = load(
        cleaned,
        source_name=SOURCE_NAME,
        source_url=WHO_BASE_URL,
        source_description="WHO Global Health Observatory OData API",
        indicator_metadata={
            indicator_code: {
                "indicator_name": _indicator_name(raw_file),
            }
        },
    )
    logger.info("Imported %d observations for WHO indicator %s", count, indicator_code)
    return count


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    import_who()


if __name__ == "__main__":
    main()
