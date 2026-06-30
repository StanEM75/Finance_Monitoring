import duckdb

def load_raw_tables():
    con = duckdb.connect("../warehouse/financial.duckdb")

    con.execute("""
        CREATE OR REPLACE TABLE raw_stock_data AS
        SELECT *
        FROM read_csv_auto('data/stock_data.csv', HEADER=TRUE)
    """)

    con.execute("""
        CREATE OR REPLACE TABLE raw_statement_data AS
        SELECT *
        FROM read_csv_auto('data/df_statement.csv', HEADER=TRUE)
    """)

    con.execute("""
        CREATE OR REPLACE TABLE raw_open_positions_data AS
        SELECT *
        FROM read_csv_auto('data/df_open_positions.csv', HEADER=TRUE)
    """)

    con.execute("""
        CREATE OR REPLACE TABLE raw_performance_data AS
        SELECT *
        FROM read_csv_auto('data/df_performance.csv', HEADER=TRUE)
    """)

    con.close()

if __name__ == "__main__":
    load_raw_tables()