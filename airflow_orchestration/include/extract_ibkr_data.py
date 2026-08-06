# ================================================================================
#                                     PACKAGES
# ================================================================================

from __future__ import annotations

import csv
import logging
from collections import defaultdict
from pathlib import Path

import pandas as pd


# ================================================================================
#                         EXTRACT AND TRANSFORM IBKR DATA
# ================================================================================

def extract_ibkr_data(
    input_path: str = "/usr/local/airflow/include/data/ibkr_extract.csv",
    output_directory: str = "/usr/local/airflow/include/data",
) -> dict[str, int | str]:
    """Extract the relevant tables from an IBKR Flex Query CSV export."""

    # ============================================================================
    #                              PARSE IBKR REPORT
    # ============================================================================

    # Parse every HEADER and DATA row into one DataFrame per IBKR section.
    def parse_report(path: Path) -> dict[str, pd.DataFrame]:
        # Store data rows separately from their section headers.
        sections: defaultdict[str, list[list[str]]] = defaultdict(list)
        headers: dict[str, list[str]] = {}

        # utf-8-sig supports exports both with and without a UTF-8 BOM.
        with path.open(encoding="utf-8-sig", newline="") as file:
            for row in csv.reader(file):
                # Rows without a row type and section name are not usable.
                if len(row) < 2:
                    continue

                row_type, section = row[:2]

                if row_type == "HEADER":
                    headers[section] = row[2:]
                elif row_type == "DATA":
                    sections[section].append(row[2:])

        # Build a DataFrame only after checking each row against its header.
        tables: dict[str, pd.DataFrame] = {}
        for section, rows in sections.items():
            columns = headers.get(section)
            if columns is None:
                raise ValueError(
                    f"Section IBKR '{section}' has data rows but no header."
                )

            invalid_rows = [row for row in rows if len(row) != len(columns)]
            if invalid_rows:
                raise ValueError(
                    f"Section IBKR '{section}' contains {len(invalid_rows)} "
                    "row(s) whose length does not match the header."
                )

            tables[section] = pd.DataFrame(rows, columns=columns)

        return tables

    # ============================================================================
    #                                SAVE CSV TABLE
    # ============================================================================

    # Write through a temporary file to avoid leaving a partial CSV behind.
    def save_table(dataframe: pd.DataFrame, destination: Path) -> None:
        temporary_path = destination.with_suffix(".tmp")
        dataframe.to_csv(temporary_path, index=False)
        temporary_path.replace(destination)

    source = Path(input_path)
    destination_directory = Path(output_directory)

    # ============================================================================
    #                         VALIDATE AND SELECT SECTIONS
    # ============================================================================

    # Stop immediately when the upstream synchronization task produced no file.
    if not source.is_file():
        raise FileNotFoundError(f"IBKR extract not found: {source}")

    # Keep only the account, performance and open-position sections.
    tables = parse_report(source)
    required_sections = {"ACCT", "FIFO", "POST"}
    missing_sections = required_sections - tables.keys()
    if missing_sections:
        missing = ", ".join(sorted(missing_sections))
        raise ValueError(f"Missing IBKR section(s): {missing}")

    # Map each IBKR section to the raw CSV expected by the DuckDB loader.
    outputs = {
        "statement": tables["ACCT"],
        "performance": tables["FIFO"],
        "open_positions": tables["POST"],
    }
    filenames = {
        "statement": "df_statement.csv",
        "performance": "df_performance.csv",
        "open_positions": "df_open_positions.csv",
    }

    # ============================================================================
    #                              EXPORT RAW TABLES
    # ============================================================================

    # Export all datasets into the Airflow shared include directory.
    destination_directory.mkdir(parents=True, exist_ok=True)
    for name, dataframe in outputs.items():
        save_table(dataframe, destination_directory / filenames[name])
        logging.info("Exported %s with %d rows.", name, len(dataframe))

    # ============================================================================
    #                               RETURN METADATA
    # ============================================================================

    # Return lightweight metadata suitable for an Airflow XCom value.
    return {
        "input_path": str(source),
        "output_directory": str(destination_directory),
        "statement_rows": len(outputs["statement"]),
        "performance_rows": len(outputs["performance"]),
        "open_position_rows": len(outputs["open_positions"]),
    }
