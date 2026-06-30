# ================================================================================
#                                     PACKAGES
# ================================================================================
from collections import defaultdict
import pandas as pd
import csv
import logging

logging.basicConfig(level=logging.INFO)

# ================================================================================
#                        CREATE A FUNCTION TO IMPORT IBKR DATA
# ================================================================================

# Define a function automating the parsing of IBKR reports into a dictionary of DataFrames
def parse_ibkr_report(path: str) -> dict[str, pd.DataFrame]:
    
    # sections includes all data rows
    sections = defaultdict(list)
    # headers includes all columns names for each section
    headers = {}

    # File is read in UTF-8 encoding to handle commas that can be part of cells
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f)

        # Go through every row in the CSV file
        for row in reader:

            # Rows having less than 2 columns are ignored, as they may not contain useful information
            if len(row) < 2:
                continue

            # Extract the first and second columns
            
            # The first column is the section name
            section = row[0]
            # The second column is the row type, which can be either "Header" or "Data"
            row_type = row[1]

            # If the row is an header, store the columns names from the third column onwards (2 first are just for information)
            if row_type == "Header":
                headers[section] = row[2:]

            # If the row is data, store the columns in the order mentioned by the header
            elif row_type == "Data":
                sections[section].append(row[2:])

    # Instantiate a dictionary to hold the DataFrames corresponding to each section
    dfs = {}

    # Convert the sections and their corresponding rows into pandas DataFrames

    # Navigate through each section and its corresponding rows
    for section, rows in sections.items():

        # Columns in a DataFrame = Headers in section
        columns = headers.get(section)

        # 2 conditions required to create a DataFrame with columns:
        # 1. The section must have headers (columns)
        # 2. All rows must have the same number of columns as the headers
        if columns and all(len(r) == len(columns) for r in rows):
            dfs[section] = pd.DataFrame(rows, columns=columns)
        else:
        # If the conditions are not met, create a DataFrame without columns to record errors
            dfs[section] = pd.DataFrame(rows)

    # The output of the function is a dictionary of DataFrames
    return dfs


# ================================================================================
#                               IMPORT IBKR DATA
# ================================================================================

# Apply the parsing function to the IBKR report CSV file
tables = parse_ibkr_report("../data/ibkr_extract.csv")


# ================================================================================
#                   TRANSPOSE DATA INTO TABLES (IF APPLICABLE)
# ================================================================================

def pivot_key_value_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a two-column key-value DataFrame into a single-row DataFrame.
    """

    if df.shape[1] != 2:
        raise ValueError(f"Expected 2 columns, got {df.shape[1]}.")

    key_col = df.columns[0]
    value_col = df.columns[1]

    df = (
        df
        .set_index(key_col)[value_col]
        .to_frame()
        .T
        .reset_index(drop=True)
    )

    df.columns.name = None

    return df


# ================================================================================
#                             ONLY KEEP RELEVANT TABLES
# ================================================================================

statement = pivot_key_value_table(tables["Statement"])

logging.info(f"Statement table transformed successfully. Contains {len(statement)} rows and {len(statement.columns)} columns.")

performance = tables["Synthèse de la performance réalisée et non-réalisée"]

open_positions = tables["Positions ouvertes"]

# ================================================================================
#                                       EXPORT DATA
# ================================================================================

# A table to extract the date of generation of the report
statement.to_csv("../data/df_statement.csv", index=False)

logging.info(f"Statement table exported successfully. Contains {len(statement)} rows and {len(statement.columns)} columns.")

# A table to extract the performance summary for open and closed positions, including realized and unrealized P&L
performance.to_csv("../data/df_performance.csv", index=False)

logging.info(f"Performance table exported successfully. Contains {len(performance)} rows and {len(performance.columns)} columns.")

# A table with open positions, including details such as symbol, quantity, average price, market value, and unrealized P&L
open_positions.to_csv("../data/df_open_positions.csv", index=False)

logging.info(f"Open positions table exported successfully. Contains {len(open_positions)} rows and {len(open_positions.columns)} columns.")




