import logging

from etl.import_owid import import_owid
from etl.import_who import import_who
from etl.import_worldbank import import_worldbank


logger = logging.getLogger(__name__)


def run_all() -> dict[str, object]:
    """Run source imports in dependency order: World Bank, WHO, then OWID."""
    results: dict[str, object] = {}
    failures: list[str] = []

    worldbank = import_worldbank()
    results["worldbank"] = worldbank
    failures.extend(
        f"World Bank {code}: {error}"
        for code, error in worldbank["failures"].items()
    )

    try:
        results["who"] = {"imported": import_who()}
    except Exception as exc:
        logger.exception("WHO import failed")
        results["who"] = {"failure": str(exc)}
        failures.append(f"WHO: {exc}")

    owid = import_owid()
    results["owid"] = owid
    failures.extend(
        f"OWID {code}: {error}"
        for code, error in owid["failures"].items()
    )

    if failures:
        raise RuntimeError("One or more imports failed: " + "; ".join(failures))
    return results


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    run_all()


if __name__ == "__main__":
    main()