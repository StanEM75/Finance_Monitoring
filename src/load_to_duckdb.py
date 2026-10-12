"""Load local CSVs using the same transactional loader as Airflow."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from airflow_orchestration.include.load_to_duckdb import load_to_duckdb

DB_PATH = ROOT / "warehouse" / "financial.duckdb"
DATA_PATH = ROOT / "data"


def load_raw_tables():
    return load_to_duckdb(str(DB_PATH), str(DATA_PATH))


if __name__ == "__main__":
    print(load_raw_tables())
