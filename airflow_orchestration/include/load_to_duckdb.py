# ================================================================================
#                                     PACKAGES
# ================================================================================

from __future__ import annotations

from pathlib import Path

import duckdb

# ================================================================================
#                            LOAD RAW TABLES INTO DUCKDB
# ================================================================================


def load_transactions(connection, csv_path: Path) -> None:
    """Upsert reported trades, preserving trades absent from a later report.

    The caller owns the transaction. Account + TransactionID identifies a trade.
    Raw strings avoid inference changes between empty and populated reports.
    """
    connection.execute(
        "CREATE OR REPLACE TEMP TABLE incoming_transactions AS "
        "SELECT * FROM read_csv_auto(?, HEADER=TRUE, ALL_VARCHAR=TRUE)",
        [str(csv_path)],
    )
    invalid = connection.execute("""
        SELECT count(*) FROM incoming_transactions
        WHERE nullif(trim(ClientAccountID), '') IS NULL
           OR nullif(trim(TransactionID), '') IS NULL
    """).fetchone()[0]
    duplicates = connection.execute("""
        SELECT count(*) FROM (
            SELECT ClientAccountID, TransactionID
            FROM incoming_transactions
            GROUP BY ALL HAVING count(*) > 1
        )
    """).fetchone()[0]
    if invalid or duplicates:
        raise ValueError("IBKR transactions require non-empty, unique account/transaction IDs.")

    connection.execute("""
        CREATE TABLE IF NOT EXISTS raw_transactions_data AS
        SELECT * FROM incoming_transactions WHERE FALSE
    """)
    connection.execute("CREATE TABLE IF NOT EXISTS raw_historical_transactions_data AS SELECT * FROM incoming_transactions WHERE FALSE")
    connection.execute("CREATE TABLE IF NOT EXISTS ibkr_history_coverage (client_account_id VARCHAR, start_date DATE, end_date DATE)")
    # Normalize a table created by the earlier CSV inference loader.
    connection.execute("""
        CREATE OR REPLACE TABLE raw_transactions_data AS
        SELECT CAST(COLUMNS(*) AS VARCHAR) FROM raw_transactions_data
    """)
    connection.execute("""
        DELETE FROM raw_transactions_data AS history
        USING incoming_transactions AS incoming
        WHERE history.ClientAccountID = incoming.ClientAccountID
          AND history.TransactionID = incoming.TransactionID
    """)
    connection.execute("""
        INSERT INTO raw_transactions_data BY NAME
        SELECT * FROM incoming_transactions
    """)


def load_to_duckdb(
    database_path: str = ("/usr/local/airflow/include/warehouse/financial.duckdb"),
    data_directory: str = "/usr/local/airflow/include/data",
) -> dict[str, int | str]:
    """Load the pipeline CSV files into DuckDB raw tables."""

    # ============================================================================
    #                         MAP TABLES TO SOURCE FILES
    # ============================================================================

    # Associate each raw DuckDB table with its upstream CSV file.
    table_sources = {
        "raw_stock_data": "stock_data.csv",
        "raw_statement_data": "df_statement.csv",
        "raw_open_positions_data": "df_open_positions.csv",
        "raw_performance_data": "df_performance.csv",
        "raw_transactions_data": "df_transactions.csv",
    }
    source_directory = Path(data_directory)
    destination = Path(database_path)

    # ============================================================================
    #                              VALIDATE INPUTS
    # ============================================================================

    # Validate all inputs before opening the database or replacing any table.
    missing_files = [
        source_directory / filename
        for filename in table_sources.values()
        if not (source_directory / filename).is_file()
    ]
    if missing_files:
        missing = ", ".join(str(path) for path in missing_files)
        raise FileNotFoundError(f"Missing source CSV file(s): {missing}")

    # Create the warehouse directory when the Airflow volume is initialized.
    destination.parent.mkdir(parents=True, exist_ok=True)
    row_counts: dict[str, int] = {}

    # ============================================================================
    #                           LOAD TABLES IN A TRANSACTION
    # ============================================================================

    # Load all raw tables in one transaction to keep the warehouse consistent.
    with duckdb.connect(str(destination)) as connection:
        connection.execute("BEGIN TRANSACTION")
        try:
            for table_name, filename in table_sources.items():
                csv_path = (source_directory / filename).resolve()
                # Escape quotes before inserting a filesystem path into DuckDB SQL.
                escaped_path = str(csv_path).replace("'", "''")
                if table_name == "raw_transactions_data":
                    load_transactions(connection, csv_path)
                else:
                    connection.execute(
                        f"""
                        CREATE OR REPLACE TABLE {table_name} AS
                        SELECT *
                        FROM read_csv_auto('{escaped_path}', HEADER = TRUE)
                        """
                    )
                row_counts[table_name] = connection.execute(
                    f"SELECT count(*) FROM {table_name}"
                ).fetchone()[0]
            connection.execute("COMMIT")
        except Exception:
            # Restore every previous table if any CSV fails to load.
            connection.execute("ROLLBACK")
            raise

    # ============================================================================
    #                               RETURN METADATA
    # ============================================================================

    # Return row counts so Airflow logs and XCom expose the load result.
    return {
        "database_path": str(destination),
        **row_counts,
    }
