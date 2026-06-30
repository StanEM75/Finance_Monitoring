# ================================================================================
#                                     PACKAGES
# ================================================================================

import requests # For API calls
import os # For environment variables
from dotenv import load_dotenv # To load .env file
import pandas as pd # For data manipulation and converting JSON to DataFrame

# ================================================================================
#                            GET CREDENTIALS AND API URL
# ================================================================================

# Load environment variables from .env file | We have previously set up the .env file with our API key to avoid printing it 
load_dotenv()

# URL for the Marketstack API endpoint (endpoint is directly included within the URL)
url = "https://api.marketstack.com/v2/eod"

# Retrieve API key from environment variables
api_key = os.getenv("API_KEY")

# ================================================================================
#                       CREATE A LIST OF STOCK SYMBOLS TO MONITOR
# ================================================================================

# Retrieve the current positions in the portfolio (only current positions are interesting to get data for)
df = pd.read_csv('../data/df_open_positions.csv')

# Korean stocks will be monitored later in the future
df = df.query('Devise != "KRW"')

# Sort by the 20 highest unrealized profit/loss as we will only select them (limit 100/month for free plan)
df.sort_values(by='P/L non réalisé', ascending=False, inplace=True)

# Create a list of symbols, representing the list of stocks we want to get data for
symbols = df['Symbole'].unique().tolist()

# ================================================================================
#                                API CALL PARAMETERS 
# ================================================================================

# Parameters for the API call: API key, stocks symbols, and limit of records to fetch
params = {
    # API Key for authentication
    "access_key": api_key,
    # Comma-separated list of stock symbols
    "symbols": ",".join(symbols),
    # Limit the number of records returned to 10000 (The limit)
    "limit": 10000,
}

# ================================================================================
#                                FUNCTION TO GET DATA
# ================================================================================

# Define a function to call the API and handle potential errors
def get_stock_data(url, params):
    try:
        # Get a response from the API
        response = requests.get(url, params=params, timeout=10)
        # Raise the status of the call: success or error
        response.raise_for_status()
        # Get the result of the call through JSON format
        return response.json()
    # Handle request exceptions
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel API : {e}")
        return None

# Call the function to call the API and get stock data required
data = get_stock_data(url, params)

# Convert the 'data' part of the JSON response to a Pandas DataFrame and print the data
if data and "data" in data:
    # Extract the data from the JSON response and convert it to a Pandas DataFrame
    df = pd.DataFrame(data["data"])
    # Convert the 'date' column to datetime format
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%dT%H:%M:%S%z")
    # Print the shape of the DataFrame to be sure we have enougn data
    print(df.shape)
    # Export the dataframe to a CSV file for further analysis
    df.to_csv("../data/stock_data.csv", index=False)

else:
    print("Aucune donnée renvoyée par l'API.")