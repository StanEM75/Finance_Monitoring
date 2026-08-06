from __future__ import annotations

import csv
import logging
from collections import defaultdict
from pathlib import Path

import pandas as pd


def extract_ibkr_data(
    input_path: str = "/usr/local/airflow/include/data/ibkr_extract.csv",
    output_directory: str = "/usr/local/airflow/include/data",
) -> dict[str, int | str]:
    """Extract the relevant tables from an IBKR Flex Query CSV export."""

    def parse_report(path: Path) -> dict[str, pd.DataFrame]:
        sections: defaultdict[str, list[list[str]]] = defaultdict(list)
        headers: dict[str, list[str]] = {}

        with path.open(encoding="utf-8-sig", newline="") as file:
            for row in csv.reader(file):
                if len(row) < 2:
                    continue

                row_type, section = row[:2]

                if row_type == "HEADER":
                    headers[section] = row[2:]
                elif row_type == "DATA":
                    sections[section].append(row[2:])

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

    def save_table(dataframe: pd.DataFrame, destination: Path) -> None:
        temporary_path = destination.with_suffix(".tmp")
        dataframe.to_csv(temporary_path, index=False)
        temporary_path.replace(destination)

    source = Path(input_path)
    destination_directory = Path(output_directory)

    if not source.is_file():
        raise FileNotFoundError(f"IBKR extract not found: {source}")

    tables = parse_report(source)
    required_sections = {"ACCT", "FIFO", "POST"}
    missing_sections = required_sections - tables.keys()
    if missing_sections:
        missing = ", ".join(sorted(missing_sections))
        raise ValueError(f"Missing IBKR section(s): {missing}")

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

    destination_directory.mkdir(parents=True, exist_ok=True)
    for name, dataframe in outputs.items():
        save_table(dataframe, destination_directory / filenames[name])
        logging.info("Exported %s with %d rows.", name, len(dataframe))

    return {
        "input_path": str(source),
        "output_directory": str(destination_directory),
        "statement_rows": len(outputs["statement"]),
        "performance_rows": len(outputs["performance"]),
        "open_position_rows": len(outputs["open_positions"]),
    }
