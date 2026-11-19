from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = PROJECT_ROOT / "data" / "outputs"
OPEN_POSITIONS_PATH = OUTPUT_DIRECTORY / "open_positions.csv"
STOCK_PRICES_PATH = OUTPUT_DIRECTORY / "stock_prices.csv"
MONTHLY_PROFIT_PATH = OUTPUT_DIRECTORY / "profit_by_month.csv"
STOCK_PROFIT_PATH = OUTPUT_DIRECTORY / "profit_by_stock.csv"
EARNINGS_PATH = OUTPUT_DIRECTORY / "fmp_earnings-calendar.csv"

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
    normalized_columns = dataframe.columns.astype(str).str.strip().str.lower()
    duplicates = normalized_columns[normalized_columns.duplicated()].unique()
    if len(duplicates):
        raise ValueError(
            f"Ambiguous columns after normalization in {source_path}: "
            + ", ".join(duplicates)
        )
    dataframe.columns = normalized_columns
    missing_columns = required_columns - set(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing columns in {source_path}: {missing}")


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


@st.cache_data(show_spinner=False)
def load_profit_data(path: str, modified_at: float, kind: str) -> pd.DataFrame:
    del modified_at
    dataframe = pd.read_csv(path)
    profit_column = (
        "monthly_realized_profit_and_loss"
        if kind == "monthly"
        else "stock_realized_profit_and_loss"
    )
    required = (
        {"trade_month", "trade_year", profit_column}
        if kind == "monthly"
        else {SYMBOL_COLUMN, profit_column}
    )
    require_columns(dataframe, required, Path(path))
    dataframe[profit_column] = pd.to_numeric(dataframe[profit_column], errors="raise")
    if dataframe[profit_column].isna().any():
        raise ValueError("A realized profit value is missing from the file.")
    if kind == "monthly":
        # IBKR/dbt exports English month names; never sort these alphabetically.
        months = {
            name.lower(): number
            for number, name in enumerate(
                (
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December",
                ),
                start=1,
            )
        }
        month_numbers = (
            dataframe["trade_month"]
            .astype("string")
            .str.strip()
            .str.lower()
            .map(months)
        )
        dataframe["month_date"] = pd.to_datetime(
            {
                "year": pd.to_numeric(dataframe["trade_year"], errors="raise"),
                "month": month_numbers,
                "day": 1,
            },
            errors="raise",
        )
        if dataframe["month_date"].isna().any():
            raise ValueError("The file contains an invalid month or year.")
        return dataframe.sort_values("month_date").reset_index(drop=True)
    dataframe[SYMBOL_COLUMN] = (
        dataframe[SYMBOL_COLUMN].astype("string").str.strip().str.upper()
    )
    if dataframe[SYMBOL_COLUMN].isna().any() or dataframe[SYMBOL_COLUMN].eq("").any():
        raise ValueError("A stock symbol is missing from the file.")
    return dataframe.sort_values(
        [profit_column, SYMBOL_COLUMN], ascending=[False, True]
    ).reset_index(drop=True)


def display_realized_profits() -> None:
    st.subheader("Realized profits")
    st.caption(
        "Sales history from the exports, independent of the signal lookback period. "
        "Amounts are displayed as exported, without currency conversion."
    )
    for path, kind in ((MONTHLY_PROFIT_PATH, "monthly"), (STOCK_PROFIT_PATH, "stock")):
        title = (
            "Monthly realized profit"
            if kind == "monthly"
            else "Stocks ranked by realized profit"
        )
        st.markdown(f"#### {title}")
        if not path.is_file():
            st.info(f"{path.name} is not available yet.")
            continue
        try:
            dataframe = load_profit_data(str(path), path.stat().st_mtime, kind)
        except (OSError, ValueError, pd.errors.ParserError) as error:
            st.error(f"Unable to load {path.name}: {error}")
            continue
        if dataframe.empty:
            st.info("No realized profit data available.")
            continue
        if kind == "monthly":
            profit = "monthly_realized_profit_and_loss"
            chart = (
                alt.Chart(dataframe)
                .mark_line(point=True)
                .encode(
                    x=alt.X(
                        "month_date:T", title="Month", axis=alt.Axis(format="%m/%Y")
                    ),
                    y=alt.Y(
                        f"{profit}:Q",
                        title="Monthly realized profit",
                        scale=alt.Scale(zero=True),
                    ),
                    tooltip=[
                        alt.Tooltip("month_date:T", title="Month", format="%m/%Y"),
                        alt.Tooltip(
                            f"{profit}:Q", title="Realized profit", format=",.2f"
                        ),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(chart, width="stretch")
            st.caption("Only months included in the export are displayed.")
        else:
            profit = "stock_realized_profit_and_loss"
            count = int(
                st.number_input(
                    "Number of stocks in the ranking",
                    min_value=1,
                    max_value=len(dataframe),
                    value=min(10, len(dataframe)),
                    step=1,
                )
            )
            chart = (
                alt.Chart(dataframe.head(count))
                .mark_bar()
                .encode(
                    x=alt.X(
                        f"{profit}:Q",
                        title="Realized profit",
                        scale=alt.Scale(zero=True),
                    ),
                    y=alt.Y(
                        f"{SYMBOL_COLUMN}:N",
                        title="Ticker",
                        sort=dataframe.head(count)[SYMBOL_COLUMN].tolist(),
                    ),
                    color=alt.condition(
                        alt.datum[profit] >= 0,
                        alt.value("#16a085"),
                        alt.value("#d35454"),
                    ),
                    tooltip=[
                        alt.Tooltip(f"{SYMBOL_COLUMN}:N", title="Ticker"),
                        alt.Tooltip(
                            f"{profit}:Q", title="Realized profit", format=",.2f"
                        ),
                    ],
                )
                .properties(height=max(260, count * 28))
            )
            st.altair_chart(chart, width="stretch")
            with st.expander("View the full ranking"):
                display_table(
                    dataframe,
                    {
                        SYMBOL_COLUMN: "Ticker",
                        profit: "Realized profit",
                    },
                )


@st.cache_data(show_spinner=False)
def load_earnings_data(path: str, modified_at: float) -> pd.DataFrame:
    del modified_at
    dataframe = pd.read_csv(path)
    require_columns(dataframe, {"symbol", "date"}, Path(path))
    dataframe["symbol"] = dataframe["symbol"].astype("string").str.strip().str.upper()
    if dataframe["symbol"].isna().any() or dataframe["symbol"].eq("").any():
        raise ValueError("An earnings event is missing its ticker.")
    dataframe["date"] = pd.to_datetime(dataframe["date"], errors="raise").dt.normalize()
    if dataframe["date"].isna().any():
        raise ValueError("An earnings event is missing its announcement date.")
    for column in ("epsestimated", "epsactual", "revenueestimated", "revenueactual"):
        if column not in dataframe:
            dataframe[column] = float("nan")
        dataframe[column] = pd.to_numeric(dataframe[column], errors="raise")
    return dataframe.sort_values(["date", "symbol"]).reset_index(drop=True)


def display_earnings_calendar() -> None:
    st.subheader("Earnings calendar")
    st.caption(
        "Earnings announcements from the latest FMP export. "
        "Missing estimates or results are shown as empty values. "
        "Revenue amounts use the provider's reporting currency without conversion."
    )
    if not EARNINGS_PATH.is_file():
        st.info("The earnings calendar is not available yet. Run the FMP data task.")
        return
    try:
        earnings = load_earnings_data(str(EARNINGS_PATH), EARNINGS_PATH.stat().st_mtime)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        st.error(f"Unable to load the earnings calendar: {error}")
        return
    if earnings.empty:
        st.info("No earnings announcements in the latest export.")
        return

    first_date = earnings["date"].min().date()
    last_date = earnings["date"].max().date()
    st.caption(f"Export coverage: {first_date} to {last_date}")
    if last_date < pd.Timestamp.now(tz="Europe/Paris").date():
        st.warning("This export only contains past dates. Refresh the FMP data.")

    event_metric, ticker_metric = st.columns(2)
    event_metric.metric("Earnings announcements", len(earnings))
    ticker_metric.metric("Companies", earnings["symbol"].nunique())
    columns = {
        "symbol": "Ticker",
        "epsestimated": "Estimated EPS",
        "epsactual": "Actual EPS",
        "revenueestimated": "Estimated revenue",
        "revenueactual": "Actual revenue",
    }
    for event_date, events in earnings.groupby("date", sort=True):
        st.markdown(f"#### {event_date.strftime('%A, %B %d, %Y')}")
        st.dataframe(
            events[list(columns)].rename(columns=columns),
            hide_index=True,
            width="stretch",
            column_config={
                "Estimated EPS": st.column_config.NumberColumn(format="%.2f"),
                "Actual EPS": st.column_config.NumberColumn(format="%.2f"),
                "Estimated revenue": st.column_config.NumberColumn(format="localized"),
                "Actual revenue": st.column_config.NumberColumn(format="localized"),
            },
        )


def get_symbol_history(
    prices: pd.DataFrame,
    symbol: str,
    start_date: pd.Timestamp,
) -> pd.DataFrame:
    history = prices.loc[
        (prices[SYMBOL_COLUMN] == symbol) & (prices[PRICE_DATE_COLUMN] >= start_date)
    ].copy()

    if history.empty:
        return history

    history = history.sort_values(PRICE_DATE_COLUMN)
    latest_row = history.iloc[-1]

    latest_exchange = latest_row.get("stock_exchange_code")
    if pd.notna(latest_exchange):
        same_listing = history.loc[history["stock_exchange_code"] == latest_exchange]
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
            100 * (current_price / period_high - 1) if period_high > 0 else float("nan")
        )
        rebound_from_low = (
            100 * (current_price / period_low - 1) if period_low > 0 else float("nan")
        )
        period_return = (
            100 * (current_price / first_price - 1) if first_price > 0 else float("nan")
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
        return "INSUFFICIENT DATA"
    if row[PROFIT_COLUMN] <= 0:
        return "NO PROFIT TO TAKE"
    if row["range_position_pct"] >= high_threshold:
        return "CONSIDER SELLING / REDUCING"
    if row["range_position_pct"] <= 30:
        return "NO SELL SIGNAL"
    return "HOLD / MONITOR"


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

st.title("📈 Stock decision dashboard")
st.caption(
    "Quantitative signals based solely on historical prices. "
    "These do not constitute financial advice."
)

# Fixed analysis defaults.
lookback_months = 6
sell_high_threshold = 80
buy_low_threshold = 20
minimum_drawdown = 15
minimum_observations = 20

missing_files = [
    path for path in (OPEN_POSITIONS_PATH, STOCK_PRICES_PATH) if not path.exists()
]
if missing_files:
    st.error("Missing file(s): " + ", ".join(str(path) for path in missing_files))
    st.stop()

try:
    positions, prices = load_data(
        str(OPEN_POSITIONS_PATH),
        str(STOCK_PRICES_PATH),
        OPEN_POSITIONS_PATH.stat().st_mtime,
        STOCK_PRICES_PATH.stat().st_mtime,
    )
except (OSError, ValueError, pd.errors.ParserError) as error:
    st.error(f"Unable to load data: {error}")
    st.stop()

if positions.empty or prices.empty:
    st.warning("The files do not contain enough data for analysis.")
    st.stop()

latest_data_date = prices[PRICE_DATE_COLUMN].max()
start_date = latest_data_date - pd.DateOffset(months=lookback_months)
data_age_days = (
    pd.Timestamp.now(tz="UTC").normalize() - latest_data_date.normalize()
).days

if data_age_days > 7:
    st.warning(
        f"The latest prices are from {latest_data_date.date()} "
        f"({data_age_days} days ago). Signals may be outdated."
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
buy_candidates["signal"] = "CONSIDER BUYING"
buy_candidates = buy_candidates.sort_values(
    ["range_position_pct", "drawdown_from_high_pct"],
    ascending=[True, True],
)

metric_1, metric_2, metric_3 = st.columns(3)
metric_1.metric("Latest price date", str(latest_data_date.date()))
metric_2.metric("Positions analyzed", len(positions))
metric_3.metric("BUY candidates found", len(buy_candidates))

unrealized_tab, lows_tab, realized_tab, earnings_tab = st.tabs(
    [
        "Unrealized gains",
        "Stocks near their lowest",
        "Realized profits",
        "Earnings calendar",
    ]
)

with unrealized_tab:
    st.subheader("Positions with the highest unrealized gains")
    st.write(
        "The top five positions are ranked by unrealized gains, then compared "
        "with their price range over the six-month lookback period."
    )

    display_table(
        sell_analysis,
        {
            SYMBOL_COLUMN: "Ticker",
            PROFIT_COLUMN: "Unrealized gain",
            "current_price": "Latest price",
            "period_low": "Period low",
            "period_high": "Period high",
            "range_position_pct": "Position within range (%)",
            "drawdown_from_high_pct": "Drawdown from high (%)",
            "period_return_pct": "Period return (%)",
            "signal": "Signal",
        },
    )

    if not sell_analysis.empty:
        selected_holding = st.selectbox(
            "View price history for a holding",
            sell_analysis[SYMBOL_COLUMN].dropna().tolist(),
        )
        holding_history = get_symbol_history(
            prices,
            selected_holding,
            start_date,
        )
        st.line_chart(
            holding_history.rename(
                columns={
                    "asset_close_price": "Close",
                    "asset_low_price": "Low",
                    "asset_high_price": "High",
                }
            ),
            x=PRICE_DATE_COLUMN,
            y=["Close", "Low", "High"],
            x_label="Date",
            y_label="Price",
            width="stretch",
            height=360,
        )

with lows_tab:
    st.subheader("Stocks not held trading near their lows")
    st.write(
        "A BUY candidate must be below the lower threshold and have "
        "fallen by at least the specified percentage from its high."
    )

    if buy_candidates.empty:
        st.info("No BUY signals currently meet all criteria.")
    else:
        display_table(
            buy_candidates,
            {
                SYMBOL_COLUMN: "Ticker",
                "current_price": "Latest price",
                "period_low": "Period low",
                "period_high": "Period high",
                "range_position_pct": "Position within range (%)",
                "drawdown_from_high_pct": "Drawdown from high (%)",
                "period_return_pct": "Period return (%)",
                "signal": "Signal",
            },
        )

        selected_candidate = st.selectbox(
            "View price history for a BUY candidate",
            buy_candidates[SYMBOL_COLUMN].tolist(),
        )
        candidate_history = get_symbol_history(
            prices,
            selected_candidate,
            start_date,
        )
        st.line_chart(
            candidate_history.rename(
                columns={
                    "asset_close_price": "Close",
                    "asset_low_price": "Low",
                    "asset_high_price": "High",
                }
            ),
            x=PRICE_DATE_COLUMN,
            y=["Close", "Low", "High"],
            x_label="Date",
            y_label="Price",
            width="stretch",
            height=360,
        )

with realized_tab:
    display_realized_profits()

with earnings_tab:
    display_earnings_calendar()

with st.expander("Methodology and limitations"):
    st.markdown(
        f"""
        - Lookback period: **{lookback_months} months**, ending on
          **{latest_data_date.date()}**.
        - A SELL signal is shown for a profitable holding when its latest
          price is in the top **{100 - sell_high_threshold}%** of its
          historical range.
        - A BUY signal is shown for a stock not held when its price is in
          the bottom **{buy_low_threshold}%** of its range and at least
          **{minimum_drawdown}%** below its high.
        - When available, price histories are compared on the same exchange.
        - A low price may reflect deteriorating fundamentals. Results do not
          account for news, valuation, risk, taxes, or personal objectives.
        """
    )
