import re
from pathlib import Path

import requests


OWID_GRAPHER_URL = "https://ourworldindata.org/grapher"
DEFAULT_TIMEOUT = 30


def _raw_dir(raw_dir: str | Path | None = None) -> Path:
    path = Path(raw_dir) if raw_dir is not None else Path("data/raw/owid")
    path.mkdir(parents=True, exist_ok=True)
    return path


def extract_owid(
    chart_slug: str,
    raw_dir: str | Path | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    force: bool = False,
) -> tuple[Path, str]:
    """Download and cache an OWID grapher chart CSV."""
    if not chart_slug or not chart_slug.strip():
        raise ValueError("chart_slug is required")

    chart_slug = chart_slug.strip().strip("/")
    output_path = _raw_dir(raw_dir) / f"{re.sub(r'[^A-Za-z0-9_.-]', '_', chart_slug)}.csv"
    request_url = f"{OWID_GRAPHER_URL}/{chart_slug}.csv?v=1&csvType=full&useColumnShortNames=false"
    if output_path.exists() and not force:
        return output_path, request_url

    response = requests.get(request_url, timeout=timeout)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type.lower():
        raise requests.RequestException(
            "OWID returned HTML instead of CSV; verify the chart slug"
        )
    if not response.content:
        raise requests.RequestException("OWID returned an empty response")
    try:
        decoded = response.content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise requests.RequestException("OWID CSV is not valid UTF-8") from exc

    lines = decoded.splitlines()
    if not lines or len(lines[0].split(",")) < 4:
        raise requests.RequestException(
            "Unexpected OWID CSV response structure"
        )

    output_path.write_text(decoded, encoding="utf-8")
    return output_path, request_url