import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time
from datetime import datetime
from utils_fetch import fetch_yahoo_or_nse   # ← new import

# ─────────────────── Streamlit page setup ────────────────────
st.set_page_config(
    page_title="Indian Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------- Dark-mode CSS (unchanged from your version) -----------
st.markdown(
    open("dark_css.txt").read(),   # optional: move the long <style> block to dark_css.txt
    unsafe_allow_html=True,
)

st.title("Indian Stock Market Dashboard")
st.markdown(
    '<div class="market-status">Real-time Indian stock prices and charts in INR</div>',
    unsafe_allow_html=True,
)

# ─────────────────── Symbol dictionaries ────────────────────
INDIAN_STOCKS = {
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    # … (rest unchanged)
}
INDIAN_INDICES = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    # … (rest unchanged)
}

# ────────────────── Utility formatters ───────────────────────
def format_inr(x):
    if x >= 10_000_000:
        return f"₹{x/10_000_000:.2f} Cr"
    if x >= 100_000:
        return f"₹{x/100_000:.2f} L"
    return f"₹{x:,.2f}"

def format_indian_number(x):
    if x >= 10_000_000:
        return f"{x/10_000_000:.2f} Cr"
    if x >= 100_000:
        return f"{x/100_000:.2f} L"
    return f"{x:,.0f}"

# ────────────────── Sidebar controls ─────────────────────────
st.sidebar.header("Chart Controls")
dtype = st.sidebar.selectbox("Data Type", ["Stocks", "Indices"])

if dtype == "Stocks":
    sel_name = st.sidebar.selectbox("Stock", list(INDIAN_STOCKS))
    symbol   = INDIAN_STOCKS[sel_name]
    custom   = st.sidebar.text_input("or enter NSE symbol", "")
    if custom:
        symbol   = custom if custom.endswith(".NS") else custom + ".NS"
        sel_name = custom.replace(".NS", "")
else:
    sel_name = st.sidebar.selectbox("Index", list(INDIAN_INDICES))
    symbol   = INDIAN_INDICES[sel_name]

period_map = {
    "1 Day": "1d", "5 Days": "5d", "1 Month": "1mo",
    "3 Months": "3mo", "6 Months": "6mo", "1 Year": "1y", "2 Years": "2y"
}
interval_map = {
    "1 Minute": "1m", "5 Minutes": "5m", "15 Minutes": "15m",
    "1 Hour": "1h", "1 Day": "1d"
}
p_label = st.sidebar.selectbox("Time Period", list(period_map), index=2)
period  = period_map[p_label]
i_label = st.sidebar.selectbox("Interval", list(interval_map), index=1)
interval = interval_map[i_label]

chart_type  = st.sidebar.selectbox("Chart Type", ["Candlestick", "Line", "Area"])
show_volume = st.sidebar.checkbox("Show Volume", value=True)
show_ma     = st.sidebar.checkbox("Show Moving Average", value=False)
ma_period   = st.sidebar.slider("MA Period", 5, 100, 20) if show_ma else 20
auto_refresh = st.sidebar.checkbox("Auto Refresh (60 s)", value=False)
if st.sidebar.button("Refresh"):
    st.rerun()

st.sidebar.caption(f"Last updated: {datetime.now():%Y-%m-%d %H:%M:%S}")

# ───────────────────── Data fetch ────────────────────────────
with st.spinner(f"Loading {sel_name} …"):
    df = fetch_yahoo_or_nse(symbol, period=period, interval=interval)

if df is None:
    st.error("❌ Unable to fetch data after several attempts.")
    st.stop()

ticker = yf.Ticker(symbol)          # still handy for company meta
info   = ticker.info

# ───────────────────── Metrics row ───────────────────────────
price = df["Close"][-1]
prev  = df["Close"][-2] if len(df) > 1 else price
delta = price - prev
pct   = delta / prev * 100 if prev else 0

market_open = 9 <= datetime.now().hour <= 15
status_txt  = "🟢 Market Open" if market_open else "🔴 Market Closed"
st.markdown(
    f'<div class="market-status"><strong>{status_txt}</strong> | NSE</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"{sel_name} Price", format_inr(price), f"₹{delta:.2f} ({pct:.2f} %)")
c2.metric("Day High", format_inr(df["High"][-1]))
c2.metric("Day Low",  format_inr(df["Low"][-1]))
c3.metric("Volume",   format_indian_number(df["Volume"][-1]))
if dtype == "Stocks" and info.get("marketCap"):
    c4.metric("Mkt Cap", f"₹{info['marketCap']/10_000_000:.2f} Cr")

# ───────────────────── Plotly chart ──────────────────────────
if show_volume:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_width=[0.7, 0.3], vertical_spacing=0.1)
else:
    fig = go.Figure()

if chart_type == "Candlestick":
    fig.add_trace(
        go.Candlestick(
            x=df.index, open=df.Open, high=df.High,
            low=df.Low, close=df.Close,
            increasing_line_color="#00ff88",
            decreasing_line_color="#ff4b4b",
            name=sel_name
        ),
        row=1, col=1 if show_volume else None
    )
elif chart_type == "Line":
    fig.add_trace(
        go.Scatter(x=df.index, y=df.Close, mode="lines",
                   line=dict(color="#00d4aa", width=3),
                   name=sel_name),
        row=1, col=1 if show_volume else None
    )
else:  # Area
    fig.add_trace(
        go.Scatter(x=df.index, y=df.Close, mode="lines",
                   fill="tozeroy",
                   line=dict(color="#00d4aa"),
                   fillcolor="rgba(0,212,170,0.3)",
                   name=sel_name),
        row=1, col=1 if show_volume else None
    )

if show_ma:
    df[f"MA{ma_period}"] = df.Close.rolling(ma_period).mean()
    fig.add_trace(
        go.Scatter(x=df.index, y=df[f"MA{ma_period}"],
                   line=dict(color="#ff9500"), name=f"MA({ma_period})"),
        row=1, col=1 if show_volume else None
    )

if show_volume:
    vol_color = ["#ff4b4b" if df.Close[i] < df.Open[i] else "#00ff88"
                 for i in range(len(df))]
    fig.add_trace(
        go.Bar(x=df.index, y=df.Volume, marker_color=vol_color,
               opacity=0.7, name="Volume"),
        row=2, col=1
    )

fig.update_layout(
    height=700,
    plot_bgcolor="#1e1e1e",
    paper_bgcolor="#0e1117",
    font_color="#fafafa",
    xaxis_rangeslider_visible=False,
    title=f"{sel_name} — {p_label} / {i_label}"
)
st.plotly_chart(fig, use_container_width=True)

# ───────────────────── Recent data table ─────────────────────
recent = df.tail(10).copy()
for col in ["Open", "High", "Low", "Close"]:
    recent[col] = recent[col].apply(lambda x: f"₹{x:.2f}")
recent["Volume"] = recent["Volume"].apply(format_indian_number)
st.markdown("### Recent Price Data")
st.dataframe(recent, use_container_width=True)

# ───────────────────── Auto-refresh ──────────────────────────
if auto_refresh:
    time.sleep(60)
    st.experimental_rerun()
