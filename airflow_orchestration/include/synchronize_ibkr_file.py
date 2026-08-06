# ================================================================================
#                                     PACKAGES
# ================================================================================

from __future__ import annotations

import shutil
from pathlib import Path


# ================================================================================
#                          SYNCHRONIZE LATEST IBKR EXTRACT
# ================================================================================

def synchronize_ibkr_file(
    source_path: str,
    destination_path: str = (
        "/usr/local/airflow/include/data/ibkr_extract.csv"
    ),
) -> dict[str, int | str]:
    """Copy the latest mounted IBKR export into the Airflow data directory."""

    # ============================================================================
    #                               VALIDATE PATHS
    # ============================================================================

    # The source must be mounted or downloaded into the Airflow worker first.
    source = Path(source_path)
    destination = Path(destination_path)

    # Validate paths before creating or replacing the destination file.
    if not source.is_file():
        raise FileNotFoundError(f"IBKR source file not found: {source}")
    if source.resolve() == destination.resolve():
        raise ValueError("Source and destination paths must be different.")

    # ============================================================================
    #                              COPY IBKR EXTRACT
    # ============================================================================

    # Copy through a temporary file so downstream tasks see a complete export.
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_suffix(".tmp")
    shutil.copy2(source, temporary_path)
    temporary_path.replace(destination)

    # ============================================================================
    #                               RETURN METADATA
    # ============================================================================

    # Return lightweight metadata suitable for an Airflow XCom value.
    return {
        "source_path": str(source),
        "destination_path": str(destination),
        "file_size_bytes": destination.stat().st_size,
    }
