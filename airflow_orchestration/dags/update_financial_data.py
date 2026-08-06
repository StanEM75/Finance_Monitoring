# ================================================================================
#                                     PACKAGES
# ================================================================================

# Mandatory imports for Airflow DAGs to work properly
from airflow.sdk import dag, task
from pendulum import datetime

# Slack notification callback
from airflow.providers.slack.notifications.slack_webhook import (
    send_slack_webhook_notification,
)

# ================================================================================
#                              PROJECT FUNCTIONS
# ================================================================================

# Import the function used to retrieve Marketstack stock data
from include.get_marketstack_data import get_marketstack_stock_data

# Import the function used to synchronize the latest IBKR extract
from include.synchronize_ibkr_file import synchronize_ibkr_file

# Import the function used to extract IBKR data into separate tables
from include.extract_ibkr_data import extract_ibkr_data

# Import the function used to load table data into DuckDB
from include.load_to_duckdb import load_to_duckdb

# ================================================================================
#                              SLACK NOTIFICATIONS
# ================================================================================

DAG_SUCCESS_NOTIFICATION = send_slack_webhook_notification(
    slack_webhook_conn_id="slack_webhook",
    text=(
        "✅ *Financial data pipeline succeeded*\n"
        "• DAG: `{{ dag.dag_id }}`\n"
        "• Run: `{{ run_id }}`\n"
        "• Execution date: `{{ logical_date }}`\n"
        "• Last task: `{{ ti.task_id }}`\n"
        "• Logs: {{ ti.log_url }}"
    ),
)

DAG_FAILURE_NOTIFICATION = send_slack_webhook_notification(
    slack_webhook_conn_id="slack_webhook",
    text=(
        "❌ *Financial data pipeline failed*\n"
        "• DAG: `{{ dag.dag_id }}`\n"
        "• Run: `{{ run_id }}`\n"
        "• Execution date: `{{ logical_date }}`\n"
        "• Failed task: `{{ ti.task_id }}`\n"
        "• Exception: `{{ exception | default('Unknown error') }}`\n"
        "• Logs: {{ ti.log_url }}"
    ),
)

# ================================================================================
#                                 DAG DEFINITION
# ================================================================================


@dag(
    dag_id="update_financial_data",
    description="Daily Marketstack and IBKR financial data pipeline",
    start_date=datetime(
        2026,
        7,
        1,
        tz="Europe/Paris",
    ),
    # Cloud Run retrieves the IBKR file at 08:00.
    # Airflow starts ten minutes later.
    schedule="10 8 * * *",
    catchup=False,
    max_active_runs=1,
    on_success_callback=DAG_SUCCESS_NOTIFICATION,
    on_failure_callback=DAG_FAILURE_NOTIFICATION,
)
def update_financial_data():
    """
    Update financial data from the Marketstack API and the latest
    Interactive Brokers extract.
    """

    # ============================================================================
    #                                  TASKS
    # ============================================================================

    @task(task_id="get_marketstack_data")
    def get_marketstack_data_task() -> dict:
        return get_marketstack_stock_data()

    @task(task_id="synchronize_ibkr_file")
    def get_latest_ibkr_file() -> None:
        return synchronize_ibkr_file(
        source_path=(
            "/usr/local/airflow/include/data/incoming/"
            "ibkr_extract.csv"
        ),
        destination_path=(
            "/usr/local/airflow/include/data/"
            "ibkr_extract.csv"
        )
                                    )

    @task(task_id="extract_ibkr_data")
    def move_ibkr_data_to_tables() -> None:
        return extract_ibkr_data()

    @task(task_id="load_to_duckdb")
    def update_duckdb() -> None:
        return load_to_duckdb()

    # ============================================================================
    #                              TASK DEPENDENCIES
    # ============================================================================

    marketstack_task = get_marketstack_data_task()
    ibkr_sync_task = get_latest_ibkr_file()
    ibkr_extract_task = move_ibkr_data_to_tables()
    duckdb_load_task = update_duckdb()

    marketstack_task >> ibkr_sync_task >> ibkr_extract_task >> duckdb_load_task


update_financial_data()