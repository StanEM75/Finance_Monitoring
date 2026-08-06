from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = PROJECT_ROOT / "data" / "outputs"
OPEN_POSITIONS_PATH = OUTPUT_DIRECTORY / "open_positions.csv"
STOCK_PRICES_PATH = OUTPUT_DIRECTORY / "stock_prices.csv"

SYMBOL_COLUMN = "asset_symbol"
PROFIT_COLUMN = "asset_unrealized_profit_and_loss"
PRICE_DATE_COLUMN = "record_date"

REQUIRED_POSITION_COLUMNS = {
    SYMBOL_COLUMN,
    PROFIT_COLUMN,
    "asset_cost_of_one_unit",
    "asset_current_value_of_one_unit",
}
REQUIRED_PRICE_COLUMNS = {
    PRICE_DATE_COLUMN,
    SYMBOL_COLUMN,
    "asset_close_price",
    "asset_low_price",
    "asset_high_price",
}


def require_columns(
    dataframe: pd.DataFrame,
    required_columns: set[str],
    source_path: Path,
) -> None:
    missing_columns = required_columns - set(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Colonnes absentes de {source_path}: {missing}")


@st.cache_data(show_spinner=False)
def load_data(
    positions_path: str,
    prices_path: str,
    positions_modified_at: float,
    prices_modified_at: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    del positions_modified_at, prices_modified_at

    positions = pd.read_csv(positions_path)
    prices = pd.read_csv(prices_path)

    require_columns(
        positions,
        REQUIRED_POSITION_COLUMNS,
        Path(positions_path),
    )
    require_columns(
        prices,
        REQUIRED_PRICE_COLUMNS,
        Path(prices_path),
    )

    positions[SYMBOL_COLUMN] = (
        positions[SYMBOL_COLUMN].astype("string").str.strip().str.upper()
    )
    positions[PROFIT_COLUMN] = pd.to_numeric(
        positions[PROFIT_COLUMN],
        errors="coerce",
    )

    for column in (
        "asset_cost_of_one_unit",
        "asset_current_value_of_one_unit",
    ):
        positions[column] = pd.to_numeric(
            positions[column],
            errors="coerce",
        )

    prices[PRICE_DATE_COLUMN] = pd.to_datetime(
        prices[PRICE_DATE_COLUMN],
        errors="coerce",
        utc=True,
    )
    prices[SYMBOL_COLUMN] = (
        prices[SYMBOL_COLUMN].astype("string").str.strip().str.upper()
    )
    for column in ("asset_close_price", "asset_low_price", "asset_high_price"):
        prices[column] = pd.to_numeric(prices[column], errors="coerce")

    positions = positions.dropna(subset=[SYMBOL_COLUMN, PROFIT_COLUMN])
    prices = prices.dropna(
        subset=[PRICE_DATE_COLUMN, SYMBOL_COLUMN, "asset_close_price"]
    )
    prices = prices.sort_values([SYMBOL_COLUMN, PRICE_DATE_COLUMN])

    return positions, prices


def get_symbol_history(
    prices: pd.DataFrame,
    symbol: str,
    start_date: pd.Timestamp,
) -> pd.DataFrame:
    history = prices.loc[
        (prices[SYMBOL_COLUMN] == symbol)
        & (prices[PRICE_DATE_COLUMN] >= start_date)
    ].copy()

    if history.empty:
        return history

    history = history.sort_values(PRICE_DATE_COLUMN)
    latest_row = history.iloc[-1]

    latest_exchange = latest_row.get("stock_exchange_code")
    if pd.notna(latest_exchange):
        same_listing = history.loc[
            history["stock_exchange_code"] == latest_exchange
        ]
        if not same_listing.empty:
            history = same_listing

    return history.sort_values(PRICE_DATE_COLUMN).drop_duplicates(
        subset=[PRICE_DATE_COLUMN],
        keep="last",
    )


def summarize_price_history(
    prices: pd.DataFrame,
    start_date: pd.Timestamp,
) -> pd.DataFrame:
    summaries: list[dict] = []

    for symbol in sorted(prices[SYMBOL_COLUMN].dropna().unique()):
        history = get_symbol_history(
            prices,
            symbol,
            start_date,
        )
        if history.empty:
            continue

        latest_row = history.iloc[-1]
        current_price = float(latest_row["asset_close_price"])
        first_price = float(history.iloc[0]["asset_close_price"])
        period_low = history["asset_low_price"].min()
        period_high = history["asset_high_price"].max()

        if pd.isna(period_low):
            period_low = history["asset_close_price"].min()
        if pd.isna(period_high):
            period_high = history["asset_close_price"].max()

        period_low = float(period_low)
        period_high = float(period_high)
        price_range = period_high - period_low

        range_position = (
            50.0
            if price_range <= 0
            else 100 * (current_price - period_low) / price_range
        )
        drawdown_from_high = (
            100 * (current_price / period_high - 1)
            if period_high > 0
            else float("nan")
        )
        rebound_from_low = (
            100 * (current_price / period_low - 1)
            if period_low > 0
            else float("nan")
        )
        period_return = (
            100 * (current_price / first_price - 1)
            if first_price > 0
            else float("nan")
        )

        summaries.append(
            {
                SYMBOL_COLUMN: symbol,
                "exchange": latest_row.get("stock_exchange_code"),
                "latest_date": latest_row[PRICE_DATE_COLUMN],
                "current_price": current_price,
                "period_low": period_low,
                "period_high": period_high,
                "range_position_pct": range_position,
                "drawdown_from_high_pct": drawdown_from_high,
                "rebound_from_low_pct": rebound_from_low,
                "period_return_pct": period_return,
                "observations": len(history),
            }
        )

    return pd.DataFrame(summaries)


def sell_signal(
    row: pd.Series,
    high_threshold: int,
    minimum_observations: int,
) -> str:
    if (
        pd.isna(row.get("observations"))
        or row.get("observations", 0) < minimum_observations
    ):
        return "DONNÉES INSUFFISANTES"
    if row[PROFIT_COLUMN] <= 0:
        return "PAS DE PRISE DE BÉNÉFICES"
    if row["range_position_pct"] >= high_threshold:
        return "SELL / ALLÉGEMENT À ÉTUDIER"
    if row["range_position_pct"] <= 30:
        return "PAS DE SIGNAL DE VENTE"
    return "CONSERVER / SURVEILLER"


def display_table(dataframe: pd.DataFrame, columns: dict[str, str]) -> None:
    display = dataframe[list(columns)].rename(columns=columns).copy()
    numeric_columns = display.select_dtypes(include="number").columns
    display[numeric_columns] = display[numeric_columns].round(2)
    st.dataframe(display, hide_index=True, width="stretch")


st.set_page_config(
    page_title="Stock decision dashboard",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Tableau de bord d'aide à la décision")
st.caption(
    "Signaux quantitatifs fondés uniquement sur l'historique des prix. "
    "Ils ne constituent pas un conseil financier."
)

with st.sidebar:
    st.header("Paramètres")
    lookback_months = st.slider("Historique analysé (mois)", 3, 12, 6)
    sell_high_threshold = st.slider(
        "Seuil haut pour SELL (%)",
        60,
        95,
        80,
    )
    buy_low_threshold = st.slider(
        "Seuil bas pour BUY (%)",
        5,
        40,
        20,
    )
    minimum_drawdown = st.slider(
        "Baisse minimale depuis le plus haut (%)",
        5,
        50,
        15,
    )
    minimum_observations = st.slider(
        "Nombre minimal d'observations",
        10,
        60,
        20,
    )

missing_files = [
    path
    for path in (OPEN_POSITIONS_PATH, STOCK_PRICES_PATH)
    if not path.exists()
]
if missing_files:
    st.error(
        "Fichier(s) introuvable(s) : "
        + ", ".join(str(path) for path in missing_files)
    )
    st.stop()

try:
    positions, prices = load_data(
        str(OPEN_POSITIONS_PATH),
        str(STOCK_PRICES_PATH),
        OPEN_POSITIONS_PATH.stat().st_mtime,
        STOCK_PRICES_PATH.stat().st_mtime,
    )
except (OSError, ValueError, pd.errors.ParserError) as error:
    st.error(f"Impossible de charger les données : {error}")
    st.stop()

if positions.empty or prices.empty:
    st.warning("Les fichiers ne contiennent pas assez de données à analyser.")
    st.stop()

latest_data_date = prices[PRICE_DATE_COLUMN].max()
start_date = latest_data_date - pd.DateOffset(months=lookback_months)
data_age_days = (
    pd.Timestamp.now(tz="UTC").normalize()
    - latest_data_date.normalize()
).days

if data_age_days > 7:
    st.warning(
        f"Les derniers prix datent du {latest_data_date.date()} "
        f"({data_age_days} jours). Les signaux peuvent être obsolètes."
    )

price_summary = summarize_price_history(
    prices,
    start_date,
)

top_positions = (
    positions.sort_values(PROFIT_COLUMN, ascending=False)
    .drop_duplicates(subset=[SYMBOL_COLUMN], keep="first")
    .head(5)
)
sell_analysis = top_positions.merge(
    price_summary,
    on=SYMBOL_COLUMN,
    how="left",
)
sell_analysis["signal"] = sell_analysis.apply(
    sell_signal,
    axis=1,
    high_threshold=sell_high_threshold,
    minimum_observations=minimum_observations,
)

held_symbols = set(positions[SYMBOL_COLUMN].dropna())
buy_candidates = price_summary.loc[
    (~price_summary[SYMBOL_COLUMN].isin(held_symbols))
    & (price_summary["observations"] >= minimum_observations)
    & (price_summary["range_position_pct"] <= buy_low_threshold)
    & (price_summary["drawdown_from_high_pct"] <= -minimum_drawdown)
].copy()
buy_candidates["signal"] = "BUY À ÉTUDIER"
buy_candidates = buy_candidates.sort_values(
    ["range_position_pct", "drawdown_from_high_pct"],
    ascending=[True, True],
)

metric_1, metric_2, metric_3 = st.columns(3)
metric_1.metric("Date des derniers prix", str(latest_data_date.date()))
metric_2.metric("Positions analysées", len(positions))
metric_3.metric("Candidats BUY détectés", len(buy_candidates))

st.subheader("1. Positions avec les plus fortes plus-values latentes")
st.write(
    "Les cinq premières positions sont classées selon leur plus-value "
    "latente, puis comparées à leur fourchette de prix sur la période."
)

display_table(
    sell_analysis,
    {
        SYMBOL_COLUMN: "Action",
        PROFIT_COLUMN: "Plus-value latente",
        "current_price": "Dernier cours",
        "period_low": "Plus bas",
        "period_high": "Plus haut",
        "range_position_pct": "Position dans la fourchette (%)",
        "drawdown_from_high_pct": "Écart au plus haut (%)",
        "period_return_pct": "Performance période (%)",
        "signal": "Signal",
    },
)

if not sell_analysis.empty:
    selected_holding = st.selectbox(
        "Afficher l'historique d'une position",
        sell_analysis[SYMBOL_COLUMN].dropna().tolist(),
    )
    holding_history = get_symbol_history(
        prices,
        selected_holding,
        start_date,
    )
    st.line_chart(
        holding_history,
        x=PRICE_DATE_COLUMN,
        y=["asset_close_price", "asset_low_price", "asset_high_price"],
        x_label="Date",
        y_label="Prix",
        width="stretch",
        height=360,
    )

st.subheader("2. Actions non détenues proches de leurs plus bas")
st.write(
    "Un candidat BUY doit être situé sous le seuil bas choisi et avoir "
    "reculé d'au moins le pourcentage défini depuis son plus haut."
)

if buy_candidates.empty:
    st.info("Aucun signal BUY ne respecte actuellement tous les critères.")
else:
    display_table(
        buy_candidates,
        {
            SYMBOL_COLUMN: "Action",
            "current_price": "Dernier cours",
            "period_low": "Plus bas",
            "period_high": "Plus haut",
            "range_position_pct": "Position dans la fourchette (%)",
            "drawdown_from_high_pct": "Écart au plus haut (%)",
            "period_return_pct": "Performance période (%)",
            "signal": "Signal",
        },
    )

    selected_candidate = st.selectbox(
        "Afficher l'historique d'un candidat BUY",
        buy_candidates[SYMBOL_COLUMN].tolist(),
    )
    candidate_history = get_symbol_history(
        prices,
        selected_candidate,
        start_date,
    )
    st.line_chart(
        candidate_history,
        x=PRICE_DATE_COLUMN,
        y=["asset_close_price", "asset_low_price", "asset_high_price"],
        x_label="Date",
        y_label="Prix",
        width="stretch",
        height=360,
    )

with st.expander("Méthode et limites"):
    st.markdown(
        f"""
        - Période analysée : **{lookback_months} mois**, terminant le
          **{latest_data_date.date()}**.
        - Un signal SELL est affiché pour une position bénéficiaire lorsque
          le dernier cours se situe dans les **{100 - sell_high_threshold}%**
          supérieurs de sa fourchette historique.
        - Un signal BUY est affiché pour une action non détenue lorsque son
          cours se situe dans les **{buy_low_threshold}%** inférieurs de sa
          fourchette et au moins **{minimum_drawdown}%** sous son plus haut.
        - Lorsque l'information est disponible, les historiques sont comparés
          sur une même place de cotation.
        - Un prix bas peut refléter une détérioration fondamentale. Les
          résultats n'intègrent ni actualités, ni valorisation, ni risque,
          ni fiscalité, ni objectifs personnels.
        """
    )
