
# Finance Monitoring

![Finance Monitoring](https://images.stockcake.com/public/a/f/6/af68f328-44b1-4763-bf96-48f017274d4a_large/trader-monitoring-data-stockcake.jpg)

### Overview

Monitor a stock portfolio, analyze market trends, and track investment performance.

## Tech Stack

| Technology | Purpose |
|---|---|
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) | Query APIs, data extraction and processing |
| ![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=flat&logo=pydantic&logoColor=white) | API configuration and data validation |
| ![DuckDB](https://img.shields.io/badge/DuckDB-FFF000?style=flat&logo=duckdb&logoColor=black) | Analytical data storage |
| ![dbt](https://img.shields.io/badge/dbt-FB542B?style=flat&logo=dbt&logoColor=white) | SQL transformations and data modeling |
| ![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-017CEE?style=flat&logo=apacheairflow&logoColor=white) / ![Astro](https://img.shields.io/badge/Astro-5C4EE5?style=flat&logo=astronomer&logoColor=white) | Pipeline orchestration |
| ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white) / ![Altair](https://img.shields.io/badge/Altair-1F77B4?style=flat&logoColor=white) | Interactive dashboard and visualizations |
| ![Ruff](https://img.shields.io/badge/Ruff-D7FF64?style=flat&logo=ruff&logoColor=black) / ![pre-commit](https://img.shields.io/badge/pre--commit-FAB040?style=flat&logo=precommit&logoColor=black) | Code quality |
## Data Sources

| Source | Purpose |
|---|---|
| [**Marketstack API**](https://marketstack.com/) | Historical stock market prices |
| **Broker data** | Manual extracts imported by the user to analyze investment performance against market trends |

## Pipeline Architecture

The project follows four main steps:

### 1. Data Ingestion

- Retrieve portfolio positions and transactions from manually imported exports.
- Fetch historical stock prices through the Marketstack API.
- Validate API parameters and handle request errors using Pydantic and Python.

### 2. Data Storage

- Store financial datasets in DuckDB for accessing data locally.

### 3. Data Transformation

- Use dbt to transform raw financial data into analysis-ready models.
- Calculate portfolio performance metrics, including realized and unrealized profits.

### 4. Data Visualization

- Build an interactive Streamlit dashboard to explore portfolio performance and historical market prices.
- Visualize investment returns, stock price trends and realized profits by month or asset.

## Dashboard Features

- **Portfolio overview:** Monitor current positions and unrealized gains or losses.
- **Stock price analysis:** Explore historical prices and market trends.
- **Realized profit tracking:** Analyze realized profits by month and stock.

## Project Structure

- `src/` — Python scripts for API extraction and Streamlit visualization.
- `transformation_of_all_data/` — dbt transformations and analytical models.
- `airflow_orchestration/` — Workflow orchestration with Astro.
- `data/` — Input datasets and generated analytical outputs.

*Personal project focused on financial analytics, data engineering and pipeline orchestration.*
