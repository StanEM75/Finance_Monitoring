import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go

# --- Load Data ---
csv_path = '../data/outputs/processed_financial_data.csv'
txt_path = '../data/reference_files/my_portfolio.txt'

@st.cache_data
def load_data():
    df = pd.read_csv(csv_path)
    with open(txt_path, 'r') as f:
        lines = f.readlines()
    portfolio_tickers = []
    for line in lines:
        if '"' in line:
            ticker = line.split('"')[1]
            portfolio_tickers.append(ticker)
    return df, portfolio_tickers

df, portfolio_tickers = load_data()

# --- Detect columns dynamically ---
date_col = [c for c in df.columns if 'date' in c.lower()][0]
symbol_col = 'symbol' if 'symbol' in df.columns else [c for c in df.columns if 'symbol' in c.lower()][0]
close_col = [c for c in df.columns if 'close' in c.lower() and 'usd' in c.lower()][0]

df[symbol_col] = df[symbol_col].astype(str)
portfolio_tickers = [t for t in portfolio_tickers if t in df[symbol_col].unique()]

# Prepare date
if not np.issubdtype(df[date_col].dtype, np.datetime64):
    df[date_col] = pd.to_datetime(df[date_col])

# 6 months window
df = df.sort_values(date_col)
max_date = df[date_col].max()
six_months_ago = max_date - pd.DateOffset(months=6)
df6 = df[df[date_col] >= six_months_ago]

# --- Analysis per ticker ---
def analyze_ticker(ticker):
    dft = df6[df6[symbol_col] == ticker].sort_values(date_col)
    if len(dft) < 30:
        return None
    prices = dft[close_col].values
    dates = dft[date_col].values
    # Trend
    trend = (prices[-1] - prices[0]) / prices[0]
    # Momentum
    ma5 = dft[close_col].rolling(5).mean().iloc[-1]
    ma20 = dft[close_col].rolling(20).mean().iloc[-1]
    momentum = ma5 - ma20
    # Volatility
    vol = dft[close_col].rolling(20).std().iloc[-1]
    vol_level = 'high' if vol > dft[close_col].mean() * 0.07 else ('medium' if vol > dft[close_col].mean() * 0.04 else 'low')
    # Peaks/bottoms (manual, no scipy)
    local_max = []
    local_min = []
    for i in range(5, len(prices)-5):
        window = prices[i-5:i+6]
        if prices[i] == np.max(window):
            local_max.append(i)
        if prices[i] == np.min(window):
            local_min.append(i)
    last_price = prices[-1]
    recent_lows = [prices[i] for i in local_min[-3:]] if len(local_min) > 0 else []
    recent_highs = [prices[i] for i in local_max[-3:]] if len(local_max) > 0 else []
    near_low = len(recent_lows) > 0 and last_price <= np.min(recent_lows) * 1.03
    near_high = len(recent_highs) > 0 and last_price >= np.max(recent_highs) * 0.98
    return {
        'trend': trend,
        'momentum': momentum,
        'volatility': vol_level,
        'last_price': last_price,
        'near_low': near_low,
        'near_high': near_high,
        'dates': dates,
        'prices': prices,
        'local_max': local_max,
        'local_min': local_min,
        'recent_lows': recent_lows,
        'recent_highs': recent_highs,
        'ma5': ma5,
        'ma20': ma20
    }

# --- Recommendation logic ---
recommendations = []
analysis = {}
for ticker in portfolio_tickers:
    res = analyze_ticker(ticker)
    if res is not None:
        analysis[ticker] = res

# Pick 2-3 tickers with strongest actionable signals
focus_tickers = []
# 1. SELL/trim at local high
for t, r in analysis.items():
    if r['near_high']:
        focus_tickers.append(t)
# 2. BUY on dip at local low
for t, r in analysis.items():
    if r['near_low'] and t not in focus_tickers:
        focus_tickers.append(t)
# 3. Fill up to 3 with highest volatility
if len(focus_tickers) < 3:
    sorted_by_vol = sorted(analysis.items(), key=lambda x: {'high':2,'medium':1,'low':0}[x[1]['volatility']], reverse=True)
    for t, r in sorted_by_vol:
        if t not in focus_tickers:
            focus_tickers.append(t)
        if len(focus_tickers) == 3:
            break
focus_tickers = focus_tickers[:3]

# --- Recommendation text ---
def get_recommendation(ticker, r):
    if r['near_high']:
        if r['trend'] > 0.05:
            return "SELL LIGHT", "Opportunistic", "Price is at a local high after a strong uptrend. Consider trimming profits."
        else:
            return "SELL LIGHT", "Optional", "Price is at a local high, but trend is weak. Trimming is optional."
    elif r['near_low']:
        if r['trend'] < -0.05:
            return "BUY ON DIP (optional)", "Optional / low priority", "Price is near a local low, but trend is negative. Only for patient investors."
        else:
            return "BUY ON DIP (strong)", "Opportunistic", "Price is near a local low and trend is stable. Good entry for a small allocation."
    else:
        return "HOLD", "No action", "No strong signal today."

# --- Streamlit UI ---
st.title("Daily Tech Stock Advisor")

st.markdown("**Today's recommended focus tickers:**")
default_focus = focus_tickers
selected = st.multiselect("Select your focus tickers of the day", options=portfolio_tickers, default=default_focus)

for ticker in selected:
    if ticker not in analysis:
        st.warning(f"No sufficient data for {ticker}")
        continue
    r = analysis[ticker]
    verdict, urgency, rationale = get_recommendation(ticker, r)
    st.subheader(f"{ticker}: {verdict} ({urgency})")
    st.markdown(f"**Rationale:** {rationale}")
    st.markdown(f"**6-month trend:** {r['trend']*100:.1f}%  \n**Momentum (5d-20d):** {r['momentum']:.2f}  \n**Volatility:** {r['volatility']}  \n**Last price:** {r['last_price']:.2f}")

    # Price chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=r['dates'], y=r['prices'], mode='lines+markers', name='Close Price'))
    fig.add_trace(go.Scatter(x=[r['dates'][i] for i in r['local_max']], y=[r['prices'][i] for i in r['local_max']],
                             mode='markers', marker=dict(color='red', size=8), name='Local Peaks'))
    fig.add_trace(go.Scatter(x=[r['dates'][i] for i in r['local_min']], y=[r['prices'][i] for i in r['local_min']],
                             mode='markers', marker=dict(color='green', size=8), name='Local Bottoms'))
    fig.add_trace(go.Scatter(x=r['dates'], y=pd.Series(r['prices']).rolling(5).mean(), mode='lines', name='MA5', line=dict(dash='dot', color='blue')))
    fig.add_trace(go.Scatter(x=r['dates'], y=pd.Series(r['prices']).rolling(20).mean(), mode='lines', name='MA20', line=dict(dash='dot', color='orange')))
    fig.update_layout(title=f"{ticker} - Last 6 months", xaxis_title="Date", yaxis_title="Price", height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Justification chart: show last price vs recent lows/highs
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=[r['dates'][-1]], y=[r['last_price']], mode='markers+text', marker=dict(color='black', size=14), name='Current Price', text=['Current'], textposition='top center'))
    if r['recent_lows']:
        for i, low in enumerate(r['recent_lows']):
            fig2.add_trace(go.Scatter(x=[r['dates'][r['local_min'][-3+i]]], y=[low], mode='markers', marker=dict(color='green', size=10), name=f'Recent Low {i+1}'))
    if r['recent_highs']:
        for i, high in enumerate(r['recent_highs']):
            fig2.add_trace(go.Scatter(x=[r['dates'][r['local_max'][-3+i]]], y=[high], mode='markers', marker=dict(color='red', size=10), name=f'Recent High {i+1}'))
    fig2.update_layout(title=f"{ticker} - Current vs Recent Lows/Highs", xaxis_title="Date", yaxis_title="Price", height=300)
    st.plotly_chart(fig2, use_container_width=True)

# --- Summary ---
st.markdown("### Daily Summary")
for ticker in default_focus:
    if ticker in analysis:
        verdict, urgency, rationale = get_recommendation(ticker, analysis[ticker])
        st.markdown(f"**{ticker}: {verdict}** ({urgency}) — {rationale}")

st.info("Each BUY suggestion is capped at 200€ per ticker for today. SELL actions are opportunistic unless otherwise noted. No action is urgent unless specified.")
