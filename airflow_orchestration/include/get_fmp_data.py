"""Fetch a FMP Stable endpoint and export its records to CSV."""

from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
import requests
from dotenv import load_dotenv

API_URL = "https://financialmodelingprep.com/stable/"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_fmp_data(
    endpoint: str = "earnings-calendar",
    params: dict[str, str] | None = None,
    output_path: str | Path | None = None,
    env_path: str | Path | None = None,
) -> dict:
    """Request FMP using FMP_API_KEY and return lightweight Airflow metadata.

    Existing environment variables take priority over the repository's .env.
    Pass an explicit env_path when using a different deployment layout.
    """
    # Validate the endpoint before attaching credentials to a request.
    endpoint = endpoint.strip()
    if not endpoint or any(
        character not in "abcdefghijklmnopqrstuvwxyz0123456789-"
        for character in endpoint
    ):
        raise ValueError("L'endpoint doit être un nom FMP Stable, ex. search-symbol.")

    request_params = dict(params) if params is not None else {}
    if "apikey" in request_params:
        raise ValueError("La clé API doit provenir de FMP_API_KEY uniquement.")
    if endpoint == "earnings-calendar":
        # Business days mean Monday-Friday; exchange holidays are not excluded.
        next_business_day = (pd.Timestamp(date.today()) + pd.offsets.BDay(1)).date()
        request_params.setdefault("from", next_business_day.isoformat())
        start_date = date.fromisoformat(request_params["from"])
        request_params.setdefault(
            "to", (pd.Timestamp(start_date) + pd.offsets.BDay(1)).date().isoformat()
        )
        if date.fromisoformat(request_params["to"]) < start_date:
            raise ValueError("La date 'to' doit être postérieure ou égale à 'from'.")
    if endpoint == "search-symbol":
        request_params.setdefault("query", "AAPL")
        if not request_params["query"].strip():
            raise ValueError("Le paramètre query ne peut pas être vide.")

    load_dotenv(Path(env_path) if env_path else PROJECT_ROOT / ".env", override=False)
    api_key = os.getenv("FMP_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "La variable FMP_API_KEY n'est pas définie dans .env ou l'environnement."
        )

    # Avoid including requests exceptions: their URL contains the API key.
    try:
        response = requests.get(
            API_URL + endpoint,
            params={**request_params, "apikey": api_key},
            timeout=30,
            allow_redirects=False,
        )
    except requests.RequestException:
        raise RuntimeError("Échec réseau lors de l'appel FMP.") from None

    if response.status_code != 200:
        raise RuntimeError(f"Échec de l'appel FMP : HTTP {response.status_code}.")
    try:
        payload = response.json()
    except ValueError:
        raise ValueError("La réponse FMP n'est pas un JSON valide.") from None

    # FMP may return an error object even with HTTP 200; do not persist it.
    if isinstance(payload, dict):
        raise RuntimeError("FMP a retourné un objet d'erreur ou un format inattendu.")
    if not isinstance(payload, list) or any(
        not isinstance(row, dict) for row in payload
    ):
        raise ValueError("La réponse FMP doit être une liste d'enregistrements JSON.")
    if not payload:
        raise ValueError(
            "FMP n'a retourné aucune donnée ; le CSV existant est conservé."
        )

    # Preserve FMP's field names and values, including camelCase and nulls.
    dataframe = pd.DataFrame(payload).drop_duplicates().reset_index(drop=True)
    destination = (
        Path(output_path)
        if output_path is not None
        else Path(__file__).resolve().parent / "data" / f"fmp_{endpoint}.csv"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            dataframe.to_csv(temporary_file, index=False)
        temporary_path.replace(destination)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return {
        "endpoint": endpoint,
        "params": request_params,
        "rows_received": len(payload),
        "rows_saved": len(dataframe),
        "output_path": str(destination),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="earnings-calendar")
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Paramètre FMP ; option répétable (ex. --param query=AAPL).",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--env-file", type=Path)
    arguments = parser.parse_args()
    parameters = {}
    for parameter in arguments.param:
        name, separator, value = parameter.partition("=")
        if not separator or not name.strip():
            parser.error("Chaque --param doit respecter NAME=VALUE.")
        parameters[name.strip()] = value
    try:
        metadata = get_fmp_data(
            endpoint=arguments.endpoint,
            params=parameters,
            output_path=arguments.output,
            env_path=arguments.env_file,
        )
    except (ValueError, RuntimeError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(metadata, ensure_ascii=False))
