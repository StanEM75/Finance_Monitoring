import requests
import os
from dotenv import load_dotenv
import polars as pl

def run_fetch_stocks(
    output_path="/usr/local/airflow/include/financial_api/outputs/stock_data.csv",
    env_path="/usr/local/airflow/include/.env"
):
    # Load env variables from the correct path
    load_dotenv(env_path)

    url = "https://api.marketstack.com/v2/eod"
    api_key = os.getenv("API_KEY")

    symbols = ["TSLA", "NVDA", "MSFT", "AMZN", "RACE"]

    params = {
        "access_key": api_key,
        "symbols": ",".join(symbols),
        "limit": 365
    }

    def get_stock_data(url, params):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return None

    data = get_stock_data(url, params)

    if data and "data" in data:
        df = pl.from_dicts(data["data"])
        df = df.with_columns(
            pl.col("date").str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S%z")
        )

        print(f"Fetched {df.shape[0]} rows")

        # Create directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        df.write_csv(output_path)
        return f"Saved to {output_path}"

    else:
        print("No data returned by API.")
        return "no_data"
