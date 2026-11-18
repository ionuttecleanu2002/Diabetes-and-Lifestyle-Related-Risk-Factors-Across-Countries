-- 1. Observation counts per indicator and source.
SELECT s.source_name, i.indicator_code, i.indicator_name, COUNT(o.observation_id) AS observation_count
FROM indicator AS i
JOIN source AS s ON s.source_id = i.source_id
LEFT JOIN observation AS o ON o.indicator_id = i.indicator_id
GROUP BY s.source_name, i.indicator_code, i.indicator_name
ORDER BY s.source_name, i.indicator_code;

-- 2. First and last observation years per indicator.
SELECT i.indicator_code, MIN(o.year) AS first_year, MAX(o.year) AS last_year
FROM indicator AS i
LEFT JOIN observation AS o ON o.indicator_id = i.indicator_id
GROUP BY i.indicator_code
ORDER BY i.indicator_code;

-- 3. Romania: life expectancy versus health spending by year.
WITH life_expectancy AS (
    SELECT o.year, o.value
    FROM observation AS o
    JOIN indicator AS i ON i.indicator_id = o.indicator_id
    WHERE o.country_iso3 = 'ROU' AND i.indicator_code = 'LIFE-EXPECTANCY'
),
health_spending AS (
    SELECT o.year, o.value
    FROM observation AS o
    JOIN indicator AS i ON i.indicator_id = o.indicator_id
    WHERE o.country_iso3 = 'ROU' AND i.indicator_code = 'SH.XPD.CHEX.GD.ZS'
)
SELECT COALESCE(l.year, h.year) AS year,
       l.value AS life_expectancy,
       h.value AS health_spending_percent_gdp
FROM life_expectancy AS l
FULL OUTER JOIN health_spending AS h USING (year)
ORDER BY year;

-- 4. Import history and counts.
SELECT il.import_id, s.source_name, il.started_at, il.finished_at,
       il.status, il.records_imported, il.error_message
FROM import_log AS il
JOIN source AS s ON s.source_id = il.source_id
ORDER BY il.started_at, il.import_id;

-- 5. Country coverage and region counts.
SELECT COUNT(*) AS country_count FROM country;

SELECT COALESCE(region, '(unknown)') AS region, COUNT(*) AS country_count
FROM country
GROUP BY region
ORDER BY region;

-- 6. Duplicate observations for the database natural key.
SELECT country_iso3, indicator_id, year, sex, age_group, COUNT(*) AS duplicate_count
FROM observation
GROUP BY country_iso3, indicator_id, year, sex, age_group
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, country_iso3, indicator_id, year;

-- 7. Minimum, maximum, and average values per indicator.
SELECT i.indicator_code, MIN(o.value) AS minimum_value,
       MAX(o.value) AS maximum_value, AVG(o.value) AS average_value
FROM indicator AS i
LEFT JOIN observation AS o ON o.indicator_id = i.indicator_id
GROUP BY i.indicator_code
ORDER BY i.indicator_code;

-- 8. Invalid sex codes; a clean result returns no rows.
SELECT sex, COUNT(*) AS row_count
FROM observation
WHERE sex NOT IN ('BTSX', 'MLE', 'FMLE')
GROUP BY sex
ORDER BY sex;

-- 9. Missing values and years outside the supported window.
SELECT
    COUNT(*) FILTER (WHERE value IS NULL) AS missing_value_count,
    COUNT(*) FILTER (WHERE year < 2000 OR year > 2024) AS out_of_window_year_count
FROM observation;

-- 10. Latest import count compared with all currently stored rows per source.
-- ImportLog is source-level (not indicator-level), so these figures are not
-- directly comparable when the source has multiple indicators or import runs.
WITH latest_import AS (
    SELECT DISTINCT ON (source_id)
           source_id, import_id, started_at, records_imported
    FROM import_log
    WHERE status = 'success'
    ORDER BY source_id, started_at DESC, import_id DESC
),
stored_counts AS (
    SELECT i.source_id, COUNT(o.observation_id) AS stored_observations
    FROM indicator AS i
    LEFT JOIN observation AS o ON o.indicator_id = i.indicator_id
    GROUP BY i.source_id
)
SELECT s.source_name, li.import_id, li.started_at,
       li.records_imported AS latest_import_rows,
       COALESCE(sc.stored_observations, 0) AS stored_observations
FROM latest_import AS li
JOIN source AS s ON s.source_id = li.source_id
LEFT JOIN stored_counts AS sc ON sc.source_id = li.source_id
ORDER BY s.source_name;

-- 11. Countries without life-expectancy observations.
SELECT c.country_iso3, c.country_name
FROM country AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM observation AS o
    JOIN indicator AS i ON i.indicator_id = o.indicator_id
    WHERE o.country_iso3 = c.country_iso3
      AND i.indicator_code = 'LIFE-EXPECTANCY'
)
ORDER BY c.country_name;

-- Source-value comparison template: compare these stored values with the
-- corresponding source dataset for the same country and year.
WITH requested(source_name, indicator_code, country_iso3, year) AS (
    VALUES
        ('WHO GHO', 'WHOSIS_000001', 'ROU', 2020),
        ('World Bank', 'SH.XPD.CHEX.GD.ZS', 'ROU', 2020),
        ('Our World in Data', 'LIFE-EXPECTANCY', 'ROU', 2020)
)
SELECT requested.source_name, requested.indicator_code,
       requested.country_iso3, requested.year, o.value AS stored_value
FROM requested
LEFT JOIN indicator AS i
       ON i.indicator_code = requested.indicator_code
LEFT JOIN observation AS o
       ON o.indicator_id = i.indicator_id
      AND o.country_iso3 = requested.country_iso3
      AND o.year = requested.year
      AND o.sex = 'BTSX'
ORDER BY requested.source_name;

-- Seven data-quality checks.
-- A. Invalid ISO3-shaped values (the country foreign key also enforces lookup membership).
SELECT COUNT(*) AS invalid_country_code_rows
FROM observation
WHERE country_iso3 !~ '^[A-Z]{3}$';

-- B. Duplicate natural keys.
SELECT COUNT(*) AS duplicate_key_groups
FROM (
    SELECT 1
    FROM observation
    GROUP BY country_iso3, indicator_id, year, sex, age_group
    HAVING COUNT(*) > 1
) AS duplicate_groups;

-- C. Missing observation values.
SELECT COUNT(*) AS missing_observation_values
FROM observation
WHERE value IS NULL;

-- D. Years outside the allowed window.
SELECT COUNT(*) AS out_of_window_years
FROM observation
WHERE year < 2000 OR year > 2024;

-- E. Invalid sex codes.
SELECT COUNT(*) AS invalid_sex_codes
FROM observation
WHERE sex NOT IN ('BTSX', 'MLE', 'FMLE');

-- F. IQR outlier flags, grouped by indicator; these rows remain stored.
SELECT i.indicator_code,
       COUNT(*) FILTER (WHERE o.is_outlier) AS flagged_outlier_rows,
       COUNT(*) AS total_rows
FROM observation AS o
JOIN indicator AS i ON i.indicator_id = o.indicator_id
GROUP BY i.indicator_code
ORDER BY i.indicator_code;

-- G. Countries with no life-expectancy data.
SELECT COUNT(*) AS countries_without_life_expectancy
FROM country AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM observation AS o
    JOIN indicator AS i ON i.indicator_id = o.indicator_id
    WHERE o.country_iso3 = c.country_iso3
      AND i.indicator_code = 'LIFE-EXPECTANCY'
);
