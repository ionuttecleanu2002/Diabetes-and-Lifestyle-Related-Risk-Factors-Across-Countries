import json
import re
from pathlib import Path
from typing import Iterable
from urllib.parse import urlencode

import requests


WHO_BASE_URL = "https://ghoapi.azureedge.net/api"
DEFAULT_TIMEOUT = 30


def _raw_dir(raw_dir: str | Path | None = None) -> Path:
    path = Path(raw_dir) if raw_dir is not None else Path("data/raw/who")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_filename(indicator_code: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", indicator_code)


def extract_who(
    indicator_code: str,
    country_codes: Iterable[str] | None = None,
    year_range: tuple[int, int] = (2000, 2024),
    raw_dir: str | Path | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    force: bool = False,
) -> tuple[Path, str]:
    """Download and cache a WHO GHO indicator response."""
    if not indicator_code or not indicator_code.strip():
        raise ValueError("indicator_code is required")

    indicator_code = indicator_code.strip()
    countries = sorted({
        code.strip().upper()
        for code in (country_codes or [])
        if code and code.strip()
    })
    start_year, end_year = year_range
    if start_year > end_year:
        raise ValueError("year_range start must not exceed end")

    conditions = [f"IndicatorCode eq '{indicator_code}'"]
    if countries:
        country_filter = " or ".join(
            f"SpatialDim eq '{country_code}'" for country_code in countries
        )
        conditions.append(f"({country_filter})")
    conditions.append(f"TimeDim ge '{start_year}'")
    conditions.append(f"TimeDim le '{end_year}'")

    params = {"$filter": " and ".join(conditions), "$format": "json"}
    request_url = f"{WHO_BASE_URL}/{indicator_code}?{urlencode(params)}"
    output_path = _raw_dir(raw_dir) / f"{_safe_filename(indicator_code)}.json"
    if output_path.exists() and not force:
        return output_path, request_url

    next_url: str | None = request_url
    rows: list[dict] = []
    seen_urls: set[str] = set()

    while next_url:
        if next_url in seen_urls:
            raise requests.RequestException("WHO pagination loop detected")
        seen_urls.add(next_url)

        response = requests.get(next_url, timeout=timeout)
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise requests.RequestException("WHO returned invalid JSON") from exc

        if not isinstance(payload, dict) or "value" not in payload:
            raise requests.RequestException(
                "Unexpected WHO OData response structure: missing 'value'"
            )
        page_rows = payload["value"]
        if not isinstance(page_rows, list):
            raise requests.RequestException(
                "Unexpected WHO OData response structure: 'value' is not a list"
            )
        rows.extend(page_rows)
        next_url = payload.get("@odata.nextLink")

    saved_payload = {
        "@odata.context": WHO_BASE_URL + f"/$metadata#{indicator_code}",
        "value": rows,
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(saved_payload, handle, ensure_ascii=False)

    return output_path, request_url
