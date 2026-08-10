# ================================================================================
#                                     PACKAGES
# ================================================================================

import os # For environment variables
from dotenv import load_dotenv # To load .env file

from pathlib import Path
import shutil
import sys

# ================================================================================
#                                      PATHS
# ================================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Load the .env file located at the project root.
load_dotenv(PROJECT_ROOT / ".env")

source_path = os.getenv("SOURCE_PATH_IBKR_FILE")

if not source_path:
    raise ValueError(
        "The SOURCE_PATH_IBKR_FILE environment variable is not defined."
    )

SOURCE = Path(source_path).expanduser()

DESTINATION = PROJECT_ROOT / "data" / "ibkr_extract.csv"

# ================================================================================
#                              COPY LATEST IBKR EXTRACT
# ================================================================================

def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(
            f"Drive file not found: {SOURCE}"
        )

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(SOURCE, DESTINATION)

    print(f"File copied to: {DESTINATION}")
    print(f"File size: {DESTINATION.stat().st_size} bytes")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise