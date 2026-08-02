# ================================================================================
#                                     PACKAGES
# ================================================================================

from pathlib import Path
import duckdb

# ================================================================================
#                                INSTANTIATE THE PATH
# ================================================================================

ROOT = Path(__file__).resolve().parents[1]

DB_PATH = ROOT / "warehouse" / "financial.duckdb"
DATA_PATH = ROOT / "data"

def load_raw_tables():
    con = duckdb.connect(str(DB_PATH))

    con.execute(f"""
        CREATE OR REPLACE TABLE raw_stock_data AS
        SELECT *
        FROM read_csv_auto('{DATA_PATH / "stock_data.csv"}', HEADER=TRUE)
    """)

    con.execute(f"""
        CREATE OR REPLACE TABLE raw_statement_data AS
        SELECT *
        FROM read_csv_auto('{DATA_PATH / "df_statement.csv"}', HEADER=TRUE)
    """)

    con.execute(f"""
        CREATE OR REPLACE TABLE raw_open_positions_data AS
        SELECT *
        FROM read_csv_auto('{DATA_PATH / "df_open_positions.csv"}', HEADER=TRUE)
    """)

    con.execute(f"""
        CREATE OR REPLACE TABLE raw_performance_data AS
        SELECT *
        FROM read_csv_auto('{DATA_PATH / "df_performance.csv"}', HEADER=TRUE)
    """)

    con.close()

if __name__ == "__main__":
    load_raw_tables()