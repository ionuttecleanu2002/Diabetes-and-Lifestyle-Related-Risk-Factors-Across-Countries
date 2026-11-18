import csv
import logging
from pathlib import Path
from typing import Callable, Iterable

from etl.clean import clean_observations
from etl.extract_owid import OWID_GRAPHER_URL, extract_owid
from etl.import_common import load_frame, log_cleaning_summary, valid_country_codes
from etl.transform_owid import transform_owid


logger = logging.getLogger(__name__)
SOURCE_NAME = "Our World in Data"
OWID_CHARTS = (
    ("life-expectancy", "LIFE-EXPECTANCY"),
    (
        "obesity-prevalence-adults-who-gho",
        "OBESITY-PREVALENCE-ADULTS-WHO-GHO",
    ),
)


def _value_column(raw_file: Path) -> str:
    with raw_file.open("r", encoding="utf-8-sig", newline="") as handle:
        columns = csv.DictReader(handle).fieldnames or []
    values = [name for name in columns if name not in {"Entity", "Code", "Year"}]
    if len(values) != 1:
        raise ValueError("OWID CSV must contain exactly one value column")
    return values[0]


def import_owid(
    raw_dir: str | Path = "data/raw/owid",
    *,
    charts: Iterable[tuple[str, str]] = OWID_CHARTS,
    force: bool = False,
    load_function: Callable[..., int] | None = None,
    country_codes: set[str] | None = None,
) -> dict[str, dict[str, int | str]]:
    """Transform and load cached OWID charts, fetching only absent files."""
    directory = Path(raw_dir)
    directory.mkdir(parents=True, exist_ok=True)
    load = load_function or load_frame
    valid_codes = country_codes if country_codes is not None else valid_country_codes()

    result: dict[str, dict[str, int | str]] = {
        "imported": {},
        "failures": {},
    }
    for chart_slug, indicator_code in charts:
        try:
            raw_file = directory / f"{chart_slug}.csv"
            if not raw_file.exists() or force:
                raw_file, _ = extract_owid(
                    chart_slug,
                    raw_dir=directory,
                    force=force,
                )
            frame = transform_owid(
                raw_file,
                indicator_code=indicator_code,
                valid_country_codes=valid_codes,
            )
            cleaned, removal_log = clean_observations(frame, valid_codes)
            log_cleaning_summary(SOURCE_NAME, removal_log)
            count = load(
                cleaned,
                source_name=SOURCE_NAME,
                source_url=OWID_GRAPHER_URL,
                source_description="Our World in Data Grapher CSV",
                indicator_metadata={
                    indicator_code: {
                        "indicator_name": _value_column(raw_file),
                    }
                },
            )
            result["imported"][indicator_code] = count
            logger.info(
                "Imported %d observations for OWID chart %s",
                count,
                chart_slug,
            )
        except Exception as exc:
            logger.exception("OWID import failed for chart %s", chart_slug)
            result["failures"][indicator_code] = str(exc)
    return result


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    result = import_owid()
    if result["failures"]:
        raise RuntimeError(
            "Some OWID charts failed: " + ", ".join(sorted(result["failures"]))
        )


if __name__ == "__main__":
    main()
