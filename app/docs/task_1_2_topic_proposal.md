# Task 1.2 – Topic Proposal

## Project Title
**Diabetes and Lifestyle-Related Risk Factors Across Countries**

### 1. Research Question

How are lifestyle-related risk factors, particularly obesity, physical inactivity, unhealthy dietary habits and tobacco consumption, associated with the prevalence of diabetes across different countries?

The project aims to investigate differences in diabetes prevalence between countries, identify relationships between lifestyle indicators and diabetes, and explore how these relationships change over time.

### 2. Relevance of the Topic

Diabetes is a major global public health concern, affecting populations across different geographical and socioeconomic environments. Its prevalence is associated with several lifestyle-related factors, including obesity, physical inactivity and unhealthy dietary patterns.

Understanding the relationship between these factors and diabetes prevalence is important for identifying population-level health patterns and supporting evidence-based public health policies.

This project is relevant to **United Nations Sustainable Development Goal 3 (SDG 3 – Good Health and Well-being)**, particularly its objective of reducing premature mortality from non-communicable diseases through prevention and treatment.

By combining data from multiple international sources, the application will provide a centralized platform for comparing countries, exploring historical trends and investigating potential relationships between lifestyle factors and diabetes prevalence.

### 3. Data Sources

The project will primarily use the following publicly available international data sources:

- **World Health Organization (WHO) – Global Health Observatory:** Health indicators, including diabetes prevalence, obesity and physical activity.
- **World Bank – World Development Indicators:** Country-level socioeconomic and health indicators that can provide additional context for the analysis.
- **Our World in Data (OWID):** Curated datasets covering diabetes, obesity, physical activity, dietary patterns and other lifestyle-related indicators.

These sources provide APIs or downloadable datasets that can be used to collect historical and country-level observations.

The selected indicators, their official codes, units and availability will be examined in detail in Task 1.7.

### 4. Target Users

The application is intended for the following groups:

- **Public health researchers:** To investigate associations between lifestyle-related risk factors and diabetes prevalence across countries.
- **Healthcare policymakers:** To compare national health indicators and identify areas that may require additional public health attention.
- **Students and academic researchers:** To explore international health datasets and perform comparative statistical analysis.
- **Data analysts:** To visualize historical trends, identify correlations and explore country-level health patterns.

### 5. Machine Learning Idea

The project will incorporate machine learning techniques to identify patterns and relationships in the collected data.

Two potential approaches will be explored:

**A. Country Clustering – K-Means**

K-Means clustering will be used to group countries with similar profiles based on diabetes prevalence and lifestyle-related indicators, such as obesity, physical inactivity and other available health measurements.

The objective is to identify groups of countries with comparable population-level risk profiles.

**B. Diabetes Prevalence Prediction – Random Forest Regression**

A Random Forest Regression model will be investigated to estimate country-level diabetes prevalence using lifestyle-related and socioeconomic indicators as input features.

The model will help evaluate which variables contribute most to the predictions and explore whether combinations of risk factors can explain differences in diabetes prevalence between countries.

Model performance will be evaluated using appropriate regression metrics, such as Mean Absolute Error (MAE), Root Mean Squared Error (RMSE) and R².

### 6. Project Scope

The project will focus on country-level data and historical comparisons, using the period 2000–2023 as an initial target where data availability permits.

The application will collect, clean and integrate data from the selected sources into a PostgreSQL database. FastAPI will provide the backend REST API, while Python data-processing and machine learning libraries will support the analytical components.

The results will represent population-level statistical associations and must not be interpreted as evidence of individual-level causation or individual diabetes risk.

### 7. Expected Outcome

The expected outcome is a web-based global health data platform that allows users to explore diabetes prevalence, compare lifestyle-related indicators between countries, examine historical trends and investigate country-level patterns using statistical analysis and machine learning.

The platform will provide a structured and reproducible way to analyze publicly available international health data.