import pandas as pd
import numpy as np
from currex import Currency
import datetime
import os

def process_stock_data(
    input_path="/usr/local/airflow/include/financial_api/outputs/stock_data.csv",
    output_path="/usr/local/airflow/include/financial_api/outputs/processed_financial_data.csv"
):
    # Import raw data
    financial_data = pd.read_csv(input_path)

    # Convert timestamps
    financial_data["utc_time"] = pd.to_datetime(financial_data["date"], utc=True)
    financial_data["france_time"] = financial_data["utc_time"].dt.tz_convert("Europe/Paris")
    financial_data["utc_date"] = financial_data["utc_time"].dt.date
    financial_data["france_date"] = financial_data["france_time"].dt.date
    financial_data = financial_data.drop(columns=['date'])

    # Company name mapping
    mapping_company_names = {
        'Tesla Inc': 'Tesla',
        'Microsoft Corporation': 'Microsoft',
        'NVIDIA Corp': 'NVIDIA',
        'Amazon.com Inc': 'Amazon',
        'Ferrari N.V.': 'Ferrari',
        'Race Eco Chain Limited': 'Ferrari',
        'LS 1x Tesla Tracker ETC': 'Tesla',
        'NVIDIA CORP': 'NVIDIA',
        '1X MSFT': 'Microsoft',
        '1X AMZN': 'Amazon'
    }
    financial_data['name'] = financial_data['name'].map(mapping_company_names).fillna(financial_data['name'])
    financial_data = financial_data.rename(columns={'name': 'company_name'})

    # Keep relevant columns
    columns_to_keep = [
        'france_date',
        'symbol',
        'company_name',
        'open',
        'close',
        'high',
        'low',
        'price_currency',
        'volume'
    ]
    financial_data = financial_data[columns_to_keep]

    # Convert currencies to USD
    def convert_to_usd(df, currency_column, columns_to_convert):
        df = df.copy()
        unique_currencies = df[currency_column].str.upper().unique()
        exchange_rates = {}

        for currency_code in unique_currencies:
            if currency_code == 'USD':
                exchange_rates[currency_code] = 1.0
            else:
                try:
                    currency = Currency(currency_code)
                    exchange_rates[currency_code] = currency.to('USD')
                except Exception as e:
                    print(f"Error for {currency_code}: {e}")
                    exchange_rates[currency_code] = None

        df['exchange_rate'] = df[currency_column].str.upper().map(exchange_rates)

        for column in columns_to_convert:
            df[f'{column}_in_usd'] = (
                df[column] * df['exchange_rate']
            )
        return df

    financial_data = convert_to_usd(
        financial_data,
        currency_column='price_currency',
        columns_to_convert=['open', 'close', 'high', 'low']
    )

    # Price variation within day
    financial_data['price_variation_within_the_day'] = (
        financial_data['close_in_usd'] - financial_data['open_in_usd']
    )

    # Final columns
    final_columns_to_keep = [
        'france_date',
        'symbol',
        'company_name',
        'open_in_usd',
        'close_in_usd',
        'high_in_usd',
        'low_in_usd',
        'volume',
        'price_variation_within_the_day'
    ]
    financial_data = financial_data[final_columns_to_keep]

    # Export cleaned data
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    financial_data.to_csv(output_path, index=False)

    return f"Processed data saved to {output_path}"
