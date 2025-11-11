# Import duckdb module for creating a local database that will enable us to use dbt
import duckdb

# Connect to a new in-memory DuckDB database
conn = duckdb.connect()

# Use DCL to create a table from the CSV file of stock data
conn.execute("""
    CREATE OR REPLACE TABLE stock_data AS
    SELECT
        *
    FROM
        'data/outputs/stock_data.csv'
""")

# Check that it worked
print("Table créée avec succès!")
print(conn.execute("SELECT COUNT(*) FROM stock_data").fetchone())
print(conn.execute("SELECT * FROM stock_data LIMIT 3").fetchall())

# Close the connection
conn.close()