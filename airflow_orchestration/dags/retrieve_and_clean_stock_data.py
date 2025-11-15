# Mandatory imports for Airflow DAGs to work properly
from airflow.sdk import dag, task
from pendulum import datetime

# Import the function defined in 'include/call_api.py' to call the API
from include.call_api import run_fetch_stocks

# Import the function defined in 'include/process_data.py' to clean the data
from include.process_data import process_stock_data

@dag(
    start_date=datetime(2025,11,15),
    schedule="@daily",
    catchup=False
)

def retrieve_and_clean_stock_data():

    # Define the Airflow task to retrieve data from the API
    @task
    def fetch_stock_data_task():
        # Call the function defined in 'include/call_api.py' to fetch stock data
        return run_fetch_stocks()

    # Define the Airflow task to clean the retrieved stock data
    @task 
    def clean_stock_data_task():
        # Call the function defined in 'include/process_data.py' to fetch stock data
        return process_stock_data()

    fetch_stock_data_task() >> clean_stock_data_task()

retrieve_and_clean_stock_data()