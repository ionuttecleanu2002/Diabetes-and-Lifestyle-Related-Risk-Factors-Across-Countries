# Task 1.5 — Challenges and Proposed Solutions

## General Data Integration Challenges

| Challenge | Why it happens | Proposed solution |
|---|---|---|
| Different country identifiers | WHO uses ISO3 codes, World Bank returns ISO2 and ISO3 codes, and other sources may use country names with different spellings. | Use ISO3 as the primary country identifier. Normalize country names with `pycountry` and maintain a manual exceptions dictionary. |
| Regions mixed with countries | Sources may include aggregates such as World or Sub-Saharan Africa alongside individual countries. | Keep only records matching valid country codes in the country table. Store regional aggregates separately if needed. |
| Missing values and gaps in years | Health surveys and estimates are not necessarily available every year for every country. | Store missing values as NULL, never as zero. Perform imputation only in the analysis layer and document the method. |
| Different formats and structures | WHO provides OData JSON, World Bank provides paginated JSON, and Our World in Data provides CSV files. | Implement a separate extractor for each source and normalize the output into a common structure: country_code, indicator_code, year, sex, value. |
| Duplicates and re-imports | The same indicator may be imported more than once. | Use database uniqueness constraints and PostgreSQL upsert operations to prevent duplicate records and update existing observations. |
| API changes and outages | External providers may change API endpoints or temporarily become unavailable. | Isolate each source in its own extractor, cache raw downloads in `data/raw/`, and maintain CSV fallbacks where possible. |
| Rate limits and large downloads | APIs may paginate results or limit the number of requests. | Implement pagination, filters, retries with backoff, and local caching of downloaded data. |
| Units and definitions | Similar health indicators may use different units, populations, or calculation methods. | Store units and source information in the indicator table. Do not combine incompatible measurements without documenting the differences. |
| Correlation versus causation | Country-level observational data contains confounding factors and cannot establish causality. | Present findings as associations, consider socioeconomic variables such as GDP per capita, and document analytical limitations. |
| Reproducibility | External sources may revise historical estimates over time. | Record import dates, source URLs, and the number of imported rows in the `import_log` table. |

## Topic-Specific Challenges

| Challenge | Why it happens | Proposed solution |
|---|---|---|
| Differences in diabetes prevalence estimates | Diabetes estimates may include diagnosed and undiagnosed cases, and sources may use different estimation methods or population groups. | Record the source, indicator definition, unit, and population coverage for each indicator. Avoid combining estimates that are not methodologically comparable. |
| Inconsistent lifestyle risk-factor measurements | Obesity, physical inactivity, dietary habits, and tobacco use may be measured using different survey methods, definitions, and age groups. Some indicators may rely on self-reported information. | Document each indicator's definition, unit, age group, and measurement method. Compare only compatible indicators and clearly identify limitations. |
| Differences in age and population structure | Diabetes prevalence is strongly influenced by population age structure. Countries with older populations may show higher crude prevalence even when age-standardized rates are more comparable. | Prefer age-standardized diabetes prevalence when available. Store the age-group or standardization information and distinguish crude from age-standardized estimates. |

## Conclusion

The project will address these challenges through data normalization, consistent indicator metadata, validation, database constraints, and documented analytical methods. Particular attention will be given to the comparability of diabetes prevalence and lifestyle risk-factor indicators across countries and years.