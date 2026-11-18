# Diabetes and Lifestyle-Related Risk Factors Across Countries

## Requirements and environment

- Python 3.12 or newer
- PostgreSQL 16 or newer
- Internet access for source data that is not already cached

Create and activate a virtual environment, then install the project dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The virtual environment is ignored by Git.

## PostgreSQL configuration

Create a local database role and database, or use an existing PostgreSQL account with access to the project database. For example, from a PostgreSQL administrator shell:

```sql
CREATE ROLE admin LOGIN PASSWORD 'SET_A_UNIQUE_PASSWORD';
CREATE DATABASE diabetes_health OWNER admin;
```

If the role already exists, change its password with `ALTER ROLE admin WITH LOGIN PASSWORD 'SET_A_UNIQUE_PASSWORD';`. Do not use the example password in a shared or production environment.

Create the local configuration from the placeholder file and edit the password:

```bash
cp -n .env.example .env
```

`.env` is ignored by Git and must not be committed. The application reads `DATABASE_URL` from it.

### Initialize or migrate the database

For a **new, empty database**, create the current tables from the SQLAlchemy models and mark the initial schema revision as applied:

```bash
python -m app.create_tables
alembic stamp head
```

For an **existing database with the project tables**, apply the non-destructive migration that adds `observation.is_outlier`:

```bash
alembic upgrade head
alembic current
```

The migration preserves existing observations and gives `is_outlier` a server-side `false` default. Do not initialize a non-empty existing database with `create_tables` plus `stamp`; use `alembic upgrade head`.

## Extraction and imports

Raw downloads are cached under `data/raw/{worldbank,who,owid}/` and excluded from Git. Import commands reuse saved files and only download files that are missing:

```bash
python -m etl.import_worldbank
python -m etl.import_who
python -m etl.import_owid
```

Run World Bank first: it populates the country table used to validate WHO and OWID rows. The World Bank importer includes the Lab 2 indicators and the diabetes/tobacco indicators in the existing project catalogue. The WHO importer uses `WHOSIS_000001`; the existing WHO registry ID `2381` is not treated as an OData code without source confirmation. OWID imports life expectancy and the existing adult-obesity chart.

To run all three in the required order:

```bash
python -m etl.run_import
```

Expected individual indicator failures are logged and do not prevent the importer from trying the remaining indicators. The overall command exits with an error if one or more imports fail. Imports are transactional and use PostgreSQL upserts.

## Exploration notebook

Launch Jupyter from the project root so imports resolve:

```bash
jupyter notebook notebooks/lab2_exploration.ipynb
```

The notebook reuses raw files where possible, transforms the three example sources, and inspects rows, types and missingness. It does not clean or load the observations.

## Verification and tests

Run the automated tests without live API dependencies:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Run the database verification queries after imports:

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f docs/sql/lab2_verification.sql
```

The queries cover observation counts and ranges, Romania comparisons, import history, country/region totals, duplicate keys, value summaries, sex validity, missing values, supported years, latest import counts, life-expectancy coverage, and seven data-quality checks.

## Current Lab 2 results and limitations

See [docs/lab2_results.md](docs/lab2_results.md) for measured results. At the time of the report, PostgreSQL and both OWID datasets were verified locally. WHO returned HTTP 502 and World Bank indicator requests timed out, so those source observations and comparisons are not claimed as completed.
