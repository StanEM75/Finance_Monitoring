# For data processing, pandas is enough because the dataframe has less than 1M rows
import pandas as pd

# For correlation calculation, numpy should be added
import numpy as np

# For date and time manipulation
import datetime

# For converting all currencies to US dollars
from currex import Currency

# Import the financial data got from the API call to process it
financial_data = pd.read_csv("../data/outputs/stock_data.csv")

# The native date format of MarketStack API is in UTC timezone
financial_data["utc_time"] = pd.to_datetime(financial_data["date"], utc=True)

# We also need to get a column with the Paris timezone (developer is based in France)
financial_data["france_time"] = financial_data["utc_time"].dt.tz_convert("Europe/Paris")

# Keep only the dates in dates columns as we have 1 row per day only
financial_data["utc_date"] = financial_data["utc_time"].dt.date
financial_data["france_date"] = financial_data["france_time"].dt.date

# Remove the original date column that is not in datetime format
financial_data = financial_data.drop(columns=['date'])

# Mapping of company names to unify different namings for the same company
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

# Apply the mapping to the name column
financial_data['name'] = financial_data['name'].map(mapping_company_names).fillna(financial_data['name'])

# Rename the name column
financial_data = financial_data.rename(columns={'name': 'company_name'})

# Specify the columns to keep for further analysis
columns_to_keep = [ 
                    # We only keep the French date as it is the developer's local time
                    'france_date', 
                    # We keep the symbol to identify each stock
                    'symbol',
                    # We keep the company name to identify each row
                    'company_name',
                    # We keep the opening price to compare it with the closing price
                    'open', 
                    # We keep the closing price to compare it with the opening price
                    'close',
                    # We keep the highest and lowest prices of the day for further analysis
                    'high',
                    'low',
                    # We keep the currency to know in which currency the prices are denominated
                    'price_currency',
                    # We keep the traded volume to compare quantities of stocks traded every day
                    'volume'
                ]

# Keep only the specified columns
financial_data = financial_data[columns_to_keep]

# Create a function that manages currency conversion to US dollars
def convert_to_usd(df, currency_column: str, columns_to_convert: list[str]):

    df = df.copy()

    # Get the list of unique currencies to calculate a precise exchange rate for every of them afterwards
    unique_currencies = df[currency_column].str.upper().unique()
    exchange_rates = {}
    
    # Iterate over all the currencies
    for currency_code in unique_currencies:
        # If currency is US dollar, there is nothing to change
        if currency_code == 'USD':
            exchange_rates[currency_code] = 1.0
        else:
            try:
                # Create a Currency object corresponding to the currency when it is not US dollar
                currency = Currency(currency_code)
                # To each currency, associate the amount of US dollars that is represented by the amount in the currency
                exchange_rates[currency_code] = currency.to('USD')
            except Exception as e:
                # If the operation does not work for one currency, it must be printed
                print(f"Error for {currency_code}: {e}")
                exchange_rates[currency_code] = None
    
    # Each row of the dataframe should have its corresponding exchange rate
    df['exchange_rate'] = df[currency_column].str.upper().map(exchange_rates) # Uppercase the value because it has previously been uppercased for retriving the list of unique currenciess

    # Calculate the amount in USD for each row and make the code modular by applying the transformation on a list of columns in parameters instead of the hardcoded names
    for column in columns_to_convert:
        df[f'{column}_in_usd'] = df[column] * df['exchange_rate']
        # Remove the USD in the column, which should be only numerical
        df[f'{column}_in_usd'] = df[f'{column}_in_usd'] \
                                    .astype(str) \
                                    .str.replace("USD", "", regex=False) \
                                    .str.strip() \
                                    .astype(float)
        # Convert the colum to string type to replace USD \
        # Remove USD because the column should be numerical
        # Remove useless whitespaces that could have been created by the replace function
        # Convert the column to float type again
        
    return df

# Apply the function on the financial_data dataframe
financial_data = convert_to_usd(
                                df = financial_data,
                                currency_column = 'price_currency',
                                columns_to_convert = ['open', 'close', 'high', 'low']
                                )

# Create a column to calculate the variation between opening and closing prices for each day and each company  
# The granularity is still company-date so no need to group by to get the variation for one company on one day
financial_data['price_variation_within_the_day'] = financial_data['close_in_usd'] - financial_data['open_in_usd']

# Display the final processed dataframe with only the necessary columns
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

# Export the processed data to a new CSV file for data vizzualisation 
financial_data.to_csv("../data/outputs/processed_financial_data.csv", index=False)