from __future__ import annotations

from pathlib import Path

import duckdb


def load_to_duckdb(
    database_path: str = (
        "/usr/local/airflow/include/warehouse/financial.duckdb"
    ),
    data_directory: str = "/usr/local/airflow/include/data",
) -> dict[str, int | str]:
    """Load the pipeline CSV files into DuckDB raw tables."""

    table_sources = {
        "raw_stock_data": "stock_data.csv",
        "raw_statement_data": "df_statement.csv",
        "raw_open_positions_data": "df_open_positions.csv",
        "raw_performance_data": "df_performance.csv",
    }
    source_directory = Path(data_directory)
    destination = Path(database_path)

    missing_files = [
        source_directory / filename
        for filename in table_sources.values()
        if not (source_directory / filename).is_file()
    ]
    if missing_files:
        missing = ", ".join(str(path) for path in missing_files)
        raise FileNotFoundError(f"Missing source CSV file(s): {missing}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    row_counts: dict[str, int] = {}

    with duckdb.connect(str(destination)) as connection:
        connection.execute("BEGIN TRANSACTION")
        try:
            for table_name, filename in table_sources.items():
                csv_path = (source_directory / filename).resolve()
                escaped_path = str(csv_path).replace("'", "''")
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
            connection.execute("ROLLBACK")
            raise

    return {
        "database_path": str(destination),
        **row_counts,
    }
