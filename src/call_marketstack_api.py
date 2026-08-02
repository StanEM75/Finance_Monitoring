# ================================================================================
#                                     PACKAGES
# ================================================================================

import requests # For API calls
import os # For environment variables
from dotenv import load_dotenv # To load .env file
import pandas as pd # For data manipulation and converting JSON to DataFrame

today = pd.Timestamp.now(tz="UTC")

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
df1 = pd.read_csv('../data/outputs/stocks_to_pick.csv')

# Rename the column 'asset_symbol' to 'symbol' to merge on a common column with the second dataframe later on
df1 = df1.rename(columns={'asset_symbol': 'symbol'})

# Retrieve the list of symbols not owned today but that could be interesting in the future
df2 = pd.read_csv('../data/outputs/stocks_to_monitor.csv')

df = pd.concat([df1, df2], ignore_index=True)

# Create a list of symbols, representing the list of stocks we want to get data for
symbols = df['symbol'].unique().tolist()

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
    "date_from": (
        today - pd.DateOffset(months=12)
    ).date().isoformat(),
    "date_to": today.date().isoformat(),
}

# ================================================================================
#                                FUNCTION TO GET DATA
# ================================================================================

# Define a function to call the API and handle potential errors
def get_stock_data(url, params):
    try:
        # Get a response from the API
        response = requests.get(
            url,
            params=params,
            timeout=(10, 120),
        )
        # Raise the status of the call: success or error
        response.raise_for_status()
    # Handle request exceptions
    except requests.exceptions.ConnectTimeout as error:
        raise RuntimeError(
            "Impossible de se connecter à Marketstack en 10 secondes."
        ) from error
    except requests.exceptions.ReadTimeout as error:
        raise RuntimeError(
            "Marketstack n'a pas répondu dans les 120 secondes."
        ) from error
    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Erreur lors de l'appel Marketstack : {error}"
        ) from error

    # Get the result of the call through JSON format
    payload = response.json()

    if "error" in payload:
        raise RuntimeError(
            f"Erreur renvoyée par Marketstack : {payload['error']}"
        )

    if "data" not in payload:
        raise ValueError(
            "La réponse Marketstack ne contient pas de champ 'data'."
        )

    return payload

# Call the function to call the API and get stock data required
data = get_stock_data(url, params)

# Convert the 'data' part of the JSON response to a Pandas DataFrame and print the data
df = pd.DataFrame(data["data"])

if df.empty:
    raise ValueError("Marketstack n'a renvoyé aucune donnée.")

# Convert the 'date' column to datetime format
df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce",
    utc=True,
)

# Print the shape of the DataFrame to be sure we have enougn data
print(df.shape)

# Export the dataframe to a CSV file for further analysis
df.to_csv("../data/stock_data.csv", index=False)