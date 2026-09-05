# ================================================================================
#                                     PACKAGES
# ================================================================================

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests

from pydantic import BaseModel, HttpUrl, PositiveInt, field_validator


class MarketstackConfig(BaseModel):
    api_url: HttpUrl
    api_key_variable: str
    limit: PositiveInt
    lookback_months: PositiveInt

    @field_validator("api_url")
    @classmethod
    def require_https(cls, api_url: HttpUrl) -> HttpUrl:
        if api_url.scheme != "https":
            raise ValueError("The API URL must use HTTPS.")
        return api_url

    @field_validator("api_key_variable")
    @classmethod
    def validate_api_key_variable(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "The 'api_key_variable' parameter cannot be empty."
            )

        return value


class MarketstackRequest(BaseModel):
    symbols: list[str]

    @field_validator("symbols")
    @classmethod
    def validate_symbols(cls, symbols: list[str]) -> list[str]:
        cleaned_symbols = sorted(
            {
                symbol.strip().upper()
                for symbol in symbols
                if symbol and symbol.strip()
            }
        )

        if not cleaned_symbols:
            raise ValueError(
                "At least one stock symbol is required."
            )

        return cleaned_symbols


def get_marketstack_stock_data(

    # ================================================================================
    #                                     CONSTANTS
    # ================================================================================
    symbol_sources: tuple[tuple[str, str], ...] = (
        (
            "/usr/local/airflow/include/data/outputs/stocks_to_pick.csv",
            "asset_symbol",
        ),
        (
            "/usr/local/airflow/include/data/outputs/stocks_to_monitor.csv",
            "symbol",
        ),
                                                    ),
    output_path: str = "/usr/local/airflow/include/data/stock_data.csv",
    api_url: str = "https://api.marketstack.com/v2/eod",
    api_key_variable: str = "API_KEY",
    limit: int = 10_000,
    lookback_months: int = 12,
                                ) -> dict:

    # Validate the task configuration before reading files or calling the API.
    config = MarketstackConfig(
        api_url=api_url,
        api_key_variable=api_key_variable,
        limit=limit,
        lookback_months=lookback_months,
    )

    # ================================================================================
    #                              LOAD STOCK SYMBOLS
    # ================================================================================

    def load_symbols() -> list[str]:
        # Collect symbols from held positions and from the monitoring list.
        symbol_frames = []

        for file_path, symbol_column in symbol_sources:
            path = Path(file_path)

            if not path.exists():
                raise FileNotFoundError(
                    f"Le fichier de symboles n'existe pas : {path}"
                )

            dataframe = pd.read_csv(path)

            # Fail with an explicit message if an upstream CSV changed schema.
            if symbol_column not in dataframe.columns:
                raise ValueError(
                    f"La colonne '{symbol_column}' est absente de {path}. "
                    f"Colonnes disponibles : {dataframe.columns.tolist()}"
                )

            symbols = (
                dataframe[symbol_column]
                .dropna()
                .astype(str)
                .str.strip()
                .str.upper()
            )

            symbol_frames.append(symbols)

        # Merge, deduplicate and sort symbols before building the API parameter.
        all_symbols = pd.concat(
            symbol_frames,
            ignore_index=True,
        )

        return sorted(
            symbol
            for symbol in all_symbols.unique().tolist()
            if symbol
        )

    # ================================================================================
    #                                       API CALL
    # ================================================================================

    def call_marketstack(
        symbols: list[str],
        api_key: str,
    ) -> dict:
        # Request one rolling year of end-of-day prices by default.
        today = pd.Timestamp.now(tz="UTC")
        params = {
            "access_key": api_key,
            "symbols": ",".join(symbols),
            "limit": config.limit,
            "date_from": (
                today - pd.DateOffset(months=config.lookback_months)
            ).date().isoformat(),
            "date_to": today.date().isoformat(),
        }

        try:
            # Use a timeout so an unavailable API does not block an Airflow worker.
            response = requests.get(
                str(config.api_url),
                params=params,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            raise RuntimeError(
                f"Échec de l'appel Marketstack : {error}"
            ) from error

        payload = response.json()

        # Marketstack can return an API error inside a successful HTTP response.
        if "error" in payload:
            api_error = payload["error"]

            if isinstance(api_error, dict):
                message = api_error.get("message", str(api_error))
                code = api_error.get("code", "unknown")
                raise RuntimeError(
                    f"Erreur Marketstack {code} : {message}"
                )

            raise RuntimeError(
                f"Erreur Marketstack : {api_error}"
            )

        if "data" not in payload:
            raise ValueError(
                "La réponse Marketstack ne contient pas de champ 'data'."
            )

        return payload

    # ============================================================================
    #                             TRANSFORM API RESPONSE
    # ============================================================================

    # Convert the JSON records into a clean tabular dataset.
    def transform_response(payload: dict) -> pd.DataFrame:
        dataframe = pd.DataFrame(payload["data"])

        if dataframe.empty:
            return dataframe

        if "date" in dataframe.columns:
            dataframe["date"] = pd.to_datetime(
                dataframe["date"],
                errors="coerce",
                utc=True,
            )

        deduplication_columns = [
            column
            for column in ("symbol", "date")
            if column in dataframe.columns
        ]

        if deduplication_columns:
            # Keep the latest record when the API returns duplicate observations.
            dataframe = dataframe.drop_duplicates(
                subset=deduplication_columns,
                keep="last",
            )

        return dataframe.reset_index(drop=True)

    # ============================================================================
    #                               EXPORT STOCK DATA
    # ============================================================================

    # Save atomically so downstream tasks never read a partially written CSV.
    def save_dataframe(dataframe: pd.DataFrame) -> None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = destination.with_suffix(".tmp")

        dataframe.to_csv(
            temporary_path,
            index=False,
        )

        temporary_path.replace(destination)

    # ============================================================================
    #                              RUN COMPLETE TASK
    # ============================================================================

    # Airflow injects the API key through an environment variable or secret.
    api_key = os.getenv(config.api_key_variable)

    if not api_key:
        raise ValueError(
            f"La variable d'environnement {config.api_key_variable} "
            "n'est pas définie."
        )

    request = MarketstackRequest(
        symbols=load_symbols(),
    )

    # Fetch, transform and persist the complete price history.
    payload = call_marketstack(request.symbols, api_key)
    stock_data = transform_response(payload)

    if stock_data.empty:
        raise ValueError(
            "Marketstack n'a retourné aucune donnée."
        )

    save_dataframe(stock_data)

    # ============================================================================
    #                               RETURN METADATA
    # ============================================================================

    # Return lightweight metadata suitable for an Airflow XCom value.
    return {
        "symbols_requested": len(request.symbols),
        "rows_received": len(stock_data),
        "output_path": output_path,
    }
