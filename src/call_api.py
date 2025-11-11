# Imports
import requests # For API calls
import os # For environment variables
from dotenv import load_dotenv # To load .env file
import polars as pl # For data manipulation and converting JSON to DataFrame

# Load environment variables from .env file | We have previously set up the .env file with our API key to avoid printing it 
load_dotenv()

# URL for the Marketstack API endpoint (endpoint is directly included within the URL)
url = "https://api.marketstack.com/v2/eod"

# Retrieve API key from environment variables
api_key = os.getenv("API_KEY")

# Create a list of symbols, representing the list of stocks we want to get data for
symbols = [
            "TSLA",  #Tesla
            "NVDA",  #Nvidia
            #"AAPL",  #Apple
            "MSFT",  #Microsoft
            "AMZN",  #Amazon
            #"PLTR",  #Palantir
            #"GOOGL", #Google
            #"META",  #Meta
            #"NFLX",  #Netflix
            #"INTC",  #Intel
            #"TTE",   #TotalEnergies
            "RACE",  #Ferrari
            #"UBER",  #Uber
            #"DIS",   #Disney
            #"PYPL",  #Paypal
            #"ADBE",  #Adobe
            #"CRM",   #Salesforce
            #"ORCL"  #Oracle
        ]

# Parameters for the API call: API key, stock symbol (TSLA), and limit of records to fetch
params = {
    # API Key for authentication
    "access_key": api_key,
    # Comma-separated list of stock symbols
    "symbols": ",".join(symbols),
    # Limit the number of records returned to 365 (days)
    "limit": 365  # 1 an de données
}


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

# Convert the 'data' part of the JSON response to a Polars DataFrame and print the data
if data and "data" in data:
    # Extract the data from the JSON response and convert it to a Polars DataFrame
    df = pl.from_dicts(data["data"])
    # Convert the 'date' column to datetime format
    df = df.with_columns(pl.col("date").str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S%z"))
    # Print the shape of the DataFrame to be sure we have enougn data
    print(df.shape)
    # Export the dataframe to a CSV file for further analysis
    df.write_csv("../data/outputs/stock_data.csv")

else:
    print("Aucune donnée renvoyée par l'API.")
