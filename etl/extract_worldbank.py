import json
import re
from pathlib import Path
from typing import Iterable

import requests


WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2"
DEFAULT_TIMEOUT = 30


def _raw_dir(raw_dir: str | Path | None = None) -> Path:
    path = Path(raw_dir) if raw_dir is not None else Path("data/raw/worldbank")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_filename(indicator_code: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", indicator_code)


def extract_worldbank_countries(
    raw_dir: str | Path | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    force: bool = False,
) -> tuple[Path, str]:
    """Download and cache World Bank country metadata."""
    output_path = _raw_dir(raw_dir) / "countries.json"
    request_url = f"{WORLD_BANK_BASE_URL}/country?format=json&per_page=500"
    if output_path.exists() and not force:
        return output_path, request_url

    countries: list[dict] = []
    page = 1
    while True:
        response = requests.get(
            f"{WORLD_BANK_BASE_URL}/country",
            params={"format": "json", "per_page": 500, "page": page},
            timeout=timeout,
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise requests.RequestException("World Bank returned invalid JSON") from exc

        if not isinstance(payload, list) or len(payload) != 2:
            raise requests.RequestException(
                "Unexpected World Bank countries response structure"
            )
        metadata, page_rows = payload
        if not isinstance(metadata, dict) or not isinstance(page_rows, list):
            raise requests.RequestException(
                "Unexpected World Bank countries response structure"
            )

        countries.extend(page_rows)
        total_pages = int(metadata.get("pages", 1))
        if page >= total_pages:
            break
        page += 1

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump([{"page": 1, "pages": 1, "per_page": len(countries), "total": len(countries)}, countries], handle)

    return output_path, request_url


def extract_worldbank(
    indicator_code: str,
    country_codes: Iterable[str] | None = None,
    year_range: tuple[int, int] = (2000, 2024),
    raw_dir: str | Path | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    force: bool = False,
) -> tuple[Path, str]:
    """Download and cache one World Bank indicator response."""
    if not indicator_code or not indicator_code.strip():
        raise ValueError("indicator_code is required")

    indicator_code = indicator_code.strip()
    start_year, end_year = year_range
    if start_year > end_year:
        raise ValueError("year_range start must not exceed end")

    countries = sorted({
        code.strip().upper()
        for code in (country_codes or [])
        if code and code.strip()
    })
    country_filter = ";".join(countries) if countries else "all"
    output_path = _raw_dir(raw_dir) / f"{_safe_filename(indicator_code)}.json"
    request_url = (
        f"{WORLD_BANK_BASE_URL}/country/{country_filter}/indicator/{indicator_code}"
        f"?format=json&per_page=20000&date={start_year}:{end_year}"
    )
    if output_path.exists() and not force:
        return output_path, request_url

    observations: list[dict] = []
    page = 1
    while True:
        response = requests.get(
            f"{WORLD_BANK_BASE_URL}/country/{country_filter}/indicator/{indicator_code}",
            params={
                "format": "json",
                "per_page": 20000,
                "date": f"{start_year}:{end_year}",
                "page": page,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise requests.RequestException("World Bank returned invalid JSON") from exc

        if not isinstance(payload, list) or len(payload) != 2:
            raise requests.RequestException(
                "Unexpected World Bank indicator response structure"
            )
        metadata, page_rows = payload
        if not isinstance(metadata, dict) or not isinstance(page_rows, list):
            raise requests.RequestException(
                "Unexpected World Bank indicator response structure"
            )

        observations.extend(page_rows)
        total_pages = int(metadata.get("pages", 1))
        if page >= total_pages:
            break
        page += 1

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(
            [
                {
                    "page": 1,
                    "pages": 1,
                    "per_page": len(observations),
                    "total": len(observations),
                },
                observations,
            ],
            handle,
        )

    return output_path, request_url