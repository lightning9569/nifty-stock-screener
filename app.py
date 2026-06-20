import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Screener", layout="wide")
st.title("NIFTY 50 Screener")

NIFTY50 = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "WIPRO.NS",
    "LT.NS",
    "BHARTIARTL.NS",
    "AXISBANK.NS",
    "KOTAKBANK.NS"
]


def get_rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def get_signal(rsi):
    if rsi < 30:
        return "BUY"
    elif rsi > 70:
        return "SELL"
    else:
        return "HOLD"


@st.cache_data(ttl=3600)
def load_data():
    rows = []

    for ticker in NIFTY50:
        try:
            df = yf.download(
                ticker,
                period="3mo",
                interval="1d",
                progress=False,
                auto_adjust=True
            )

            if df.empty or len(df) < 20:
                continue

            close = df["Close"].squeeze()

            rsi_series = get_rsi(close)

            rsi = float(rsi_series.iloc[-1])
            price = float(close.iloc[-1])

            change = (
                (close.iloc[-1] - close.iloc[-2])
                / close.iloc[-2]
            ) * 100

            rows.append({
                "Ticker": ticker.replace(".NS", ""),
                "Price (₹)": round(price, 2),
                "Change (%)": round(change, 2),
                "RSI": round(rsi, 1),
                "Signal": get_signal(rsi),
                "_ticker": ticker
            })

        except Exception as e:
            st.warning(f"Error loading {ticker}: {e}")

    return pd.DataFrame(rows)


with st.spinner("Fetching data..."):
    data = load_data()

if data.empty:
    st.error("No stock data could be loaded.")
    st.stop()

# ==========================
# Top Metrics
# ==========================

col1, col2, col3, col4 = st.columns(4)

col1.metric("Stocks Screened", len(data))
col2.metric("Average RSI", round(data["RSI"].mean(), 1))
col3.metric("BUY Signals", len(data[data["Signal"] == "BUY"]))
col4.metric("SELL Signals", len(data[data["Signal"] == "SELL"]))

st.divider()

# ==========================
# Filters
# ==========================

col_a, col_b = st.columns([1, 2])

with col_a:
    sig_filter = st.selectbox(
        "Filter by Signal",
        ["All", "BUY", "SELL", "HOLD"]
    )

with col_b:
    rsi_range = st.slider(
        "RSI Range",
        0,
        100,
        (0, 100)
    )

filtered = data.copy()

if sig_filter != "All":
    filtered = filtered[
        filtered["Signal"] == sig_filter
    ]

filtered = filtered[
    (filtered["RSI"] >= rsi_range[0]) &
    (filtered["RSI"] <= rsi_range[1])
]

st.subheader("Stock Overview")

def color_signal(val):
    if val == "BUY":
        return "background-color: green; color: white"
    elif val == "SELL":
        return "background-color: red; color: white"
    return ""

styled = filtered.drop(columns=["_ticker"]).style.map(
    color_signal,
    subset=["Signal"]
)

st.dataframe(styled, use_container_width=True)

# ==========================
# Chart Section
# ==========================

st.subheader("Price Chart")

selected = st.selectbox(
    "Select Stock",
    data["_ticker"].tolist()
)

hist = yf.download(
    selected,
    period="3mo",
    interval="1d",
    progress=False,
    auto_adjust=True
)

close_hist = hist["Close"].squeeze()

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=hist.index,
        y=close_hist,
        mode="lines",
        name="Price"
    )
)

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Price (₹)",
    height=450
)

st.plotly_chart(
    fig,
    use_container_width=True
)