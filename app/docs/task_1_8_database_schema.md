# Task 1.8 – Database Schema Design

## 1. Database design

The project uses a relational, star-like database schema with five tables:

| Table | Purpose |
|---|---|
| `source` | Stores the external data source name and URL. |
| `country` | Stores country information, using ISO3 as the primary key. |
| `indicator` | Stores indicator codes, names, units and their data source. |
| `observation` | Stores the measured values for each country, indicator, year, sex and age group. |
| `import_log` | Records data imports for reproducibility and auditing. |

The `observation` table is the central fact table. It references the `country` and `indicator` tables through foreign keys.
IQR outlier status is stored in the Boolean `is_outlier` column. Existing observations default to `false`; outliers remain in the database and are not deleted.

## 2. Changes for the diabetes and lifestyle project

The original schema is retained, with one additional column in the `observation` table:

**`age_group`**

This column identifies the population age group associated with an observation. It is important because the selected indicators use different age ranges. For example, diabetes prevalence covers people aged 20–79, while obesity and physical activity indicators may cover adults aged 18 and older.

The column uses a default value of `ALL` when an observation is not divided into a specific age group.

The unique constraint on observations is extended to include `age_group`. This prevents observations for different age groups from being incorrectly treated as duplicates.

## 3. Table relationships

- One source can provide multiple indicators.
- One indicator can have many observations.
- One country can have many observations.
- Each observation belongs to one country and one indicator.
- Import records are stored separately in `import_log`.

## 4. Data integrity

- ISO3 country codes identify countries.
- Foreign keys maintain relationships between tables.
- A unique constraint prevents duplicate observations for the same country, indicator, year, sex and age group.
- Missing measurements are stored as NULL, not zero.
- Numeric measurements use `NUMERIC(18,4)` to preserve decimal precision.
- An index on indicator and year supports time-series queries.

## 5. Justification

This design allows data from WHO, the World Bank and Our World in Data to be stored in a consistent structure. The additional `age_group` column supports comparisons between indicators that use different population age ranges. Keeping source and indicator metadata in separate tables avoids repeating this information for every observation. The import log supports reproducibility by recording when and from where data was imported.