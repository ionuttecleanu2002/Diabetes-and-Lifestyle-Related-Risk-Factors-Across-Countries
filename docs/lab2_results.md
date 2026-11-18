# Lab 2 Results — Global Health Data Platform

**Run date:** 2026-11-18  
**Database:** PostgreSQL 16, local `diabetes_health` database  
**Result scope:** Real database and raw OWID data; WHO and World Bank indicator API failures are reported below.

## Import results

The World Bank country endpoint succeeded and populated **217 countries** across seven regions. All six configured World Bank indicator requests (the four Lab 2 indicators plus the existing diabetes and tobacco indicators) timed out. The country metadata import was logged with zero observations; no World Bank indicator rows were loaded.

The WHO request for `WHOSIS_000001` failed with HTTP 502. It produced no WHO observation import log, and no WHO observations were loaded.

OWID successfully imported two chart datasets:

| OWID indicator | Raw rows | Rows removed by the supported-year rule | First import | Second import | Stored after second import |
|---|---:|---:|---:|---:|---:|
| `LIFE-EXPECTANCY` | 17,898 | 12,738 | 5,160 | 5,160 | 5,160 |
| `OBESITY-PREVALENCE-ADULTS-WHO-GHO` | 8,820 | 3,920 | 4,900 | 4,900 | 4,900 |

Other cleaning stages reported zero removals for the two downloaded OWID datasets. Missing values were not filled with zero. IQR outliers were kept and flagged.

### Re-import / idempotency

The initial observation table was empty. After the first OWID run it contained 10,060 observations (5,160 + 4,900). After rerunning the same cached OWID imports, it still contained **10,060 observations**. The second import logs reported the same row counts, demonstrating stable upserts for these datasets.

The import log contains five successful records: one zero-observation World Bank country metadata import and two per-chart records for each of the two OWID runs. Failed World Bank indicator and WHO requests are not logged as successful imports.

## Seven data-quality checks

| Check | Result | Explanation |
|---|---:|---|
| Invalid country-code shape | 0 rows | All observation codes match three uppercase letters. Country membership is also enforced by the database foreign key. |
| Duplicate natural-key groups | 0 | No duplicate `(country, indicator, year, sex, age_group)` groups were found. |
| Missing observation values | 0 | No stored value is `NULL`; no missing value was substituted with zero. |
| Years outside 2000–2024 | 0 | Stored observations all fall inside the requested year window. |
| Invalid sex codes | 0 | Stored codes are limited to `BTSX`, `MLE`, and `FMLE`. |
| IQR outliers flagged (retained) | 54 life-expectancy; 121 obesity | Outliers are marked `is_outlier = true`; they were not deleted. |
| Countries without life-expectancy data | 2 | `CHI` (Channel Islands) and `XKX` (Kosovo) have no OWID life-expectancy rows in the imported data. |

The database verification script also reported zero missing values and zero out-of-window years. Current counts and value ranges are available by running [docs/sql/lab2_verification.sql](sql/lab2_verification.sql).

## Romania: life expectancy and health spending

The imported OWID life-expectancy value for Romania in 2020 is **74.0464 years**. No health-spending observation was available because the World Bank indicator import timed out, so the SQL comparison has a missing health-spending value; no trend relationship is inferred.

## Comparison with original source values

| Source | Country / year | Stored value | Source value | Result |
|---|---|---:|---:|---|
| OWID life expectancy | Romania, 2020 | 74.0464 | 74.0464 in the downloaded OWID raw CSV | Matches exactly at the stored four-decimal precision. |
| WHO `WHOSIS_000001` | Romania, 2020 | Not stored | Not obtained | WHO returned HTTP 502 during extraction; comparison could not be performed. |
| World Bank `SH.XPD.CHEX.GD.ZS` | Romania, 2020 | Not stored | Not obtained | World Bank indicator requests timed out; comparison could not be performed. |

The OWID comparison used the cached original chart CSV (`life-expectancy.csv`), not an invented or independently estimated value. The WHO and World Bank comparisons remain incomplete and should be rerun when their endpoints respond.

## Limitations and next steps

- The World Bank endpoint was reachable for country metadata but timed out for indicator responses. Its six indicators must be retried.
- The WHO endpoint returned a gateway error. The `WHOSIS_000001` dataset must be retried when the endpoint is healthy.
- Because those sources have no stored indicator values, the three-source comparison requirement is not yet complete.
- The two countries without OWID life-expectancy coverage remain absent for this indicator; no values were imputed.
- The latest-import-vs-stored-count query is source-level because `import_log` has no indicator foreign key. For a source with several indicators, its latest import count is not directly comparable to the source-wide stored total.

## Reproduction

```bash
python -m etl.import_worldbank
python -m etl.import_who
python -m etl.import_owid
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f docs/sql/lab2_verification.sql
```
