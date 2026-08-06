# ================================================================================
#                                     PACKAGES
# ================================================================================

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests


def get_marketstack_stock_data(

    # ================================================================================
    #                                     CONSTANTS
    # ================================================================================
    symbol_sources: tuple[tuple[str, str], ...] = (
        (
            "/usr/local/airflow/include/data/stocks_to_pick.csv",
            "symbol",
        ),
        (
            "/usr/local/airflow/include/data/stocks_to_monitor.csv",
            "symbol",
        ),
    ),
    output_path: str = "/usr/local/airflow/include/data/stock_data.csv",
    api_url: str = "https://api.marketstack.com/v2/eod",
    api_key_variable: str = "API_KEY",
    limit: int = 10_000,
    lookback_months: int = 12,
) -> dict:

    # ================================================================================
    #                              LOAD STOCK SYMBOLS
    # ================================================================================

    def load_symbols() -> list[str]:
        symbol_frames = []

        for file_path, symbol_column in symbol_sources:
            path = Path(file_path)

            if not path.exists():
                raise FileNotFoundError(
                    f"Le fichier de symboles n'existe pas : {path}"
                )

            dataframe = pd.read_csv(path)

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
        today = pd.Timestamp.now(tz="UTC")
        params = {
            "access_key": api_key,
            "symbols": ",".join(symbols),
            "limit": limit,
            "date_from": (
                today - pd.DateOffset(months=lookback_months)
            ).date().isoformat(),
            "date_to": today.date().isoformat(),
        }

        try:
            response = requests.get(
                api_url,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            raise RuntimeError(
                f"Échec de l'appel Marketstack : {error}"
            ) from error

        payload = response.json()

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
            dataframe = dataframe.drop_duplicates(
                subset=deduplication_columns,
                keep="last",
            )

        return dataframe.reset_index(drop=True)

    def save_dataframe(dataframe: pd.DataFrame) -> None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = destination.with_suffix(".tmp")

        dataframe.to_csv(
            temporary_path,
            index=False,
        )

        temporary_path.replace(destination)

    api_key = os.getenv(api_key_variable)

    if not api_key:
        raise ValueError(
            f"La variable d'environnement {api_key_variable} "
            "n'est pas définie."
        )

    symbols = load_symbols()

    if not symbols:
        raise ValueError(
            "Aucun symbole valide n'a été trouvé dans les CSV."
        )

    payload = call_marketstack(symbols, api_key)
    stock_data = transform_response(payload)

    if stock_data.empty:
        raise ValueError(
            "Marketstack n'a retourné aucune donnée."
        )

    save_dataframe(stock_data)

    return {
        "symbols_requested": len(symbols),
        "rows_received": len(stock_data),
        "output_path": output_path,
    }
