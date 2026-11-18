import logging
from collections.abc import Iterable

import pandas as pd


logger = logging.getLogger(__name__)
REQUIRED_COLUMNS = {
    "country_iso3",
    "indicator_code",
    "year",
    "sex",
    "value",
}
VALID_SEX_CODES = {"BTSX", "MLE", "FMLE"}

PERCENTAGE_INDICATORS = {
    "SH.STA.DIAB.ZS",
    "SH.PRV.SMOK",
    "SH.XPD.CHEX.GD.ZS",
    "SH.IMM.MEAS",
    "obesity-prevalence-adults-who-gho",
    "OBESITY-PREVALENCE-ADULTS-WHO-GHO",
    "2381",
}

INDICATOR_BOUNDS = {
    "SH.STA.DIAB.ZS": (0.0, 100.0),
    "SH.PRV.SMOK": (0.0, 100.0),
    "SH.XPD.CHEX.GD.ZS": (0.0, 100.0),
    "SH.IMM.MEAS": (0.0, 100.0),
    "obesity-prevalence-adults-who-gho": (0.0, 100.0),
    "2381": (0.0, 100.0),
    "SP.DYN.IMRT.IN": (0.0, 500.0),
    "NY.GDP.PCAP.CD": (0.0, 1_000_000.0),
    "WHOSIS_000001": (0.0, 150.0),
    "OWID_LIFE_EXPECTANCY": (0.0, 150.0),
    "life-expectancy": (0.0, 150.0),
    "LIFE-EXPECTANCY": (0.0, 150.0),
}


def _record_removal(logs: list[str], count: int, reason: str) -> None:
    message = f"{count} rows removed: {reason}"
    logs.append(message)
    logger.info(message)


def add_iqr_outliers(frame: pd.DataFrame) -> pd.DataFrame:
    """Add is_outlier using the per-indicator IQR rule."""
    if frame.empty:
        result = frame.copy()
        result["is_outlier"] = pd.Series(dtype="bool")
        return result

    result = frame.copy()
    result["is_outlier"] = False
    for indicator_code, group in result.groupby("indicator_code", dropna=False):
        if len(group) < 4:
            continue
        values = pd.to_numeric(group["value"], errors="coerce").dropna()
        if len(values) < 4:
            continue
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        if pd.isna(iqr) or iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        result.loc[group.index, "is_outlier"] = (
            pd.to_numeric(result.loc[group.index, "value"], errors="coerce")
            .lt(lower)
            .fillna(False)
            | pd.to_numeric(result.loc[group.index, "value"], errors="coerce")
            .gt(upper)
            .fillna(False)
        )

    return result


def clean_observations(
    frame: pd.DataFrame,
    valid_country_codes: Iterable[str] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Clean a normalized observation frame and report removal counts."""
    missing_columns = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing_columns:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing_columns)
        )

    logs: list[str] = []
    result = frame.copy()
    initial_count = len(result)

    for column in ("country_iso3", "indicator_code", "sex"):
        result[column] = result[column].astype("string").str.strip().str.upper()

    invalid_country_count = (
        result["country_iso3"].isna()
        | result["country_iso3"].eq("")
        | result["country_iso3"].str.len().ne(3)
    ).sum()
    result = result[
        result["country_iso3"].notna()
        & result["country_iso3"].ne("")
        & result["country_iso3"].str.len().eq(3)
    ]
    _record_removal(logs, int(invalid_country_count), "missing country ISO3 codes")

    if valid_country_codes is not None:
        valid_codes = {
            str(code).strip().upper()
            for code in valid_country_codes
            if code is not None
        }
        invalid_count = (~result["country_iso3"].isin(valid_codes)).sum()
        result = result[result["country_iso3"].isin(valid_codes)]
        _record_removal(logs, int(invalid_count), "country not in country table")

    result["year"] = pd.to_numeric(result["year"], errors="coerce")
    result["value"] = pd.to_numeric(result["value"], errors="coerce")

    invalid_year_count = result["year"].isna().sum()
    result = result[result["year"].notna()]
    _record_removal(logs, int(invalid_year_count), "non-numeric or missing year")

    fractional_count = (result["year"] % 1 != 0).sum()
    result = result[result["year"] % 1 == 0]
    _record_removal(logs, int(fractional_count), "fractional year")
    result["year"] = result["year"].astype("int64")

    invalid_value_count = result["value"].isna().sum()
    result = result[result["value"].notna()]
    _record_removal(logs, int(invalid_value_count), "non-numeric or missing value")

    sex_map = {
        "": "BTSX",
        "BOTH": "BTSX",
        "BOTH SEX": "BTSX",
        "BOTH SEXES": "BTSX",
        "SEX_BOTH": "BTSX",
        "SEX_MLE": "MLE",
        "SEX_FMLE": "FMLE",
        "SEX_BTSX": "BTSX",
        "MALE": "MLE",
        "M": "MLE",
        "FEMALE": "FMLE",
        "F": "FMLE",
    }
    sex_series = result["sex"].fillna("").str.upper()
    result["sex"] = sex_series.map(sex_map).fillna(sex_series)
    result["sex"] = result["sex"].replace("", "BTSX")
    invalid_sex_count = (~result["sex"].isin(VALID_SEX_CODES)).sum()
    result = result[result["sex"].isin(VALID_SEX_CODES)]
    _record_removal(logs, int(invalid_sex_count), "invalid sex code")

    outside_window_count = (
        (result["year"] < 2000) | (result["year"] > 2024)
    ).sum()
    result = result[(result["year"] >= 2000) & (result["year"] <= 2024)]
    _record_removal(
        logs,
        int(outside_window_count),
        "year outside 2000 through 2024",
    )

    before_bounds = len(result)
    result = result[
        result.apply(
            lambda row: _value_within_bounds(
                str(row["indicator_code"]),
                float(row["value"]),
            ),
            axis=1,
        )
    ]
    bounds_count = before_bounds - len(result)
    _record_removal(
        logs,
        int(bounds_count),
        "value outside plausible indicator bounds",
    )

    duplicate_count = result.duplicated(
        subset=["country_iso3", "indicator_code", "year", "sex"],
        keep="first",
    ).sum()
    result = result.drop_duplicates(
        subset=["country_iso3", "indicator_code", "year", "sex"],
        keep="first",
    )
    _record_removal(logs, int(duplicate_count), "duplicate natural key")

    result = add_iqr_outliers(result)
    total_removed = initial_count - len(result)
    if total_removed:
        logger.info(
            "Cleaning removed %d of %d input rows",
            total_removed,
            initial_count,
        )
    return result.reset_index(drop=True), logs


def _value_within_bounds(indicator_code: str, value: float) -> bool:
    bounds = INDICATOR_BOUNDS.get(indicator_code)
    if bounds is not None:
        return bounds[0] <= value <= bounds[1]
    if indicator_code in PERCENTAGE_INDICATORS:
        return 0.0 <= value <= 100.0
    return 0.0 <= value <= 1_000_000.0


def clean_data(
    frame: pd.DataFrame,
    valid_country_codes: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Backward-friendly cleaning helper returning only the cleaned frame."""
    cleaned, _ = clean_observations(frame, valid_country_codes)
    return cleaned
