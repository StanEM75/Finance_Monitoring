# ================================================================================
#                                     PACKAGES
# ================================================================================

from pathlib import Path
import shutil
import sys

# ================================================================================
#                                      PATHS
# ================================================================================

SOURCE = Path(
    "/Users/stanislas/Library/CloudStorage/"
    "GoogleDrive-standhuart75@gmail.com/"
    "My Drive/IBKR - Extract/ibkr_extract.csv"
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DESTINATION = PROJECT_ROOT / "data" / "raw" / "ibkr_extract.csv"

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