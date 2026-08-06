# Mandatory imports for Airflow DAGs to work properly
from airflow.sdk import dag, task
from pendulum import datetime

# Import the function to call the Marketstack API and retrieve stock data
from airflow_orchestration.include.get_marketstack_data import get_marketstack_stock_data

# Import the function to call the IBKR file synchronization and get the latest IBKR extract
from airflow_orchestration.include.synchronize_ibkr_file import synchronize_ibkr_file

# Import the function to extract IBKR data from the synchronized file and put it into tables
from airflow_orchestration.include.extract_ibkr_data import extract_ibkr_data

# Import the function to load table data into DuckDB
from airflow_orchestration.include.load_to_duckdb import load_to_duckdb


@dag(
    dag_id="update_financial_data",
    start_date=datetime(2026,7,1),
    # Starts five minutes after IBKR file update everyday
    schedule="5 8 * * *",
    catchup=False
)

def update_financial_data():
    """
    DAG to update financial data from Marketstack API and IBKR extract file.
    """

    @task
    def marketstack():
        get_marketstack_stock_data()

    @task
    def ibkr_sync():
        synchronize_ibkr_file()

    @task
    def ibkr_extract():
        extract_ibkr_data()

    @task
    def duckdb():
        load_to_duckdb()

    # Define the task dependencies
    marketstack_task = marketstack()
    ibkr_sync_task = ibkr_sync()
    ibkr_extract_task = ibkr_extract()
    duckdb_load_task = duckdb()

    # Set the task dependencies
    marketstack_task >> ibkr_sync_task >> ibkr_extract_task >> duckdb_load_task


