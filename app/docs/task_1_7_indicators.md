# Task 1.7 – Analysis of External Data Sources

## 1. Selected indicators

The project investigates the relationship between diabetes prevalence and lifestyle-related risk factors across countries. The selected indicators are:

| Indicator | Code / ID | Source | Unit |
|---|---|---|---|
| Diabetes prevalence (population aged 20–79) | `SH.STA.DIAB.ZS` | World Bank – World Development Indicators; original source: International Diabetes Federation | % of population aged 20–79 |
| Obesity prevalence among adults (BMI ≥ 30) | `obesity-prevalence-adults-who-gho` (OWID chart slug) | WHO Global Health Observatory, distributed by Our World in Data | % of adults aged 18+ |
| Prevalence of current tobacco use | `SH.PRV.SMOK` | World Bank; original source: WHO Global Health Observatory | % of adults aged 15+ |
| Insufficient physical activity among adults aged 18+ | WHO Indicator Registry ID: `2381` (OData code to be confirmed) | WHO Global Health Observatory | % of adults aged 18+ |

### Indicator definitions and notes

- **Diabetes prevalence:** Percentage of people aged 20–79 with type 1 or type 2 diabetes. The estimate is adjusted to a standard population age structure.
- **Obesity prevalence:** Percentage of adults aged 18 or older with a body mass index (BMI) of at least 30 kg/m².
- **Tobacco use:** Percentage of people aged 15 or older who currently use tobacco, including smoked and smokeless tobacco. E-cigarettes are excluded.
- **Insufficient physical activity:** Percentage of adults aged 18 or older who do not meet the recommended weekly physical activity threshold.

## 2. Browser tests

The following URLs are provided for checking the data sources and response formats.

### World Bank – Diabetes prevalence

https://api.worldbank.org/v2/country/all/indicator/SH.STA.DIAB.ZS?format=json&per_page=5&date=2000:2024

Expected response: JSON containing paging information and country observations, including `countryiso3code`, `date` and `value`.

### World Bank – Tobacco use

https://api.worldbank.org/v2/country/all/indicator/SH.PRV.SMOK?format=json&per_page=5&date=2000:2024

Expected response: JSON containing paging information and country observations.

### Our World in Data – Obesity prevalence

https://ourworldindata.org/grapher/obesity-prevalence-adults-who-gho.csv?v=1&csvType=full&useColumnShortNames=false

Expected response: CSV data with country/entity names, codes, years and indicator values.

### WHO – Physical activity indicator information

https://www.who.int/data/gho/data/indicators/indicator-details/GHO/prevalence-of-insufficient-physical-activity-among-adults-aged-18-years-%28age-standardized-estimate%29-%28-%29

This page describes the indicator and its definition. The WHO Indicator Registry ID is 2381. The corresponding code for the legacy OData API must be identified before using that API endpoint.

### WHO – Search the indicator catalogue

https://ghoapi.azureedge.net/api/Indicator?$filter=contains(IndicatorName,'Physical activity')&$format=json

Expected response: JSON containing indicator codes and names, if the legacy endpoint is available.

## 3. Data source and integration considerations

- The World Bank API provides structured JSON responses and country ISO3 codes.
- Our World in Data provides CSV files that can be downloaded directly. Its datasets may include regional aggregates as well as countries, so rows must be checked before importing.
- WHO indicator definitions should be checked carefully, especially age groups, sex disaggregation and whether estimates are crude or age-standardized.
- Missing observations must remain missing rather than being interpreted as zero.
- Indicators from different sources may have different reporting years and estimation methods. Comparisons must account for these differences.

## 4. Planned scope

The initial analysis will focus on country-level observations from 2000 onward, using the most recent available year for each indicator. The exact date coverage will depend on the availability of each source.

The selected indicators will be normalized into a common structure:

`country_iso3, indicator_code, year, sex, value`

Source-specific definitions, units and metadata will be recorded in the indicator table.

## 5. References

- World Bank – Diabetes prevalence: https://data.worldbank.org/indicator/SH.STA.DIAB.ZS
- World Bank – Tobacco use metadata: https://databank.worldbank.org/metadataglossary/health-nutrition-and-population-statistics/series/SH.PRV.SMOK
- WHO / Our World in Data – Obesity prevalence: https://ourworldindata.org/grapher/obesity-prevalence-adults-who-gho
- WHO – Insufficient physical activity indicator: https://www.who.int/data/gho/data/indicators/indicator-details/GHO/prevalence-of-insufficient-physical-activity-among-adults-aged-18-years-%28age-standardized-estimate%29-%28-%29
- Our World in Data – Chart API documentation: https://docs.owid.io/projects/etl/api/chart-api/
