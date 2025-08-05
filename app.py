#!/usr/bin/env python3
# Indian Stock Dashboard on Streamlit Cloud
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pandas as pd
import yfinance as yf        # still used for company meta (cheap call)
from utils_fetch import fetch_data

# ───────────────── Streamlit page config ────────────────
st.set_page_config("Indian Stock Dashboard", "📈", layout="wide")

# ──────────────── Inline dark theme CSS ────────────────
st.markdown("""
<style>
.main .block-container{background:#0e1117;color:#fafafa}
.css-1d391kg{background:#262730}
div[data-testid="metric-container"]{background:#262730;border:1px solid #333;
  padding:1rem;border-radius:.5rem;color:#fafafa;box-shadow:0 2px 4px #0003}
h1,h2,h3{color:#00d4aa!important}.stMarkdown{color:#fafafa}
.stButton>button{background:#00d4aa;color:#0e1117;border:none;border-radius:.5rem;font-weight:700}
.stSelectbox div>div{background:#262730;color:#fafafa}
.stTextInput input{background:#262730;color:#fafafa;border:1px solid #333}
.market-status{background:#262730;padding:1rem;border-radius:.5rem;border-left:4px solid #00d4aa;margin-bottom:1rem}
</style>
""", unsafe_allow_html=True)

# ─────────────── Symbol dictionaries ───────────────────
INDIAN_STOCKS = {
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "ITC": "ITC.NS",
    "State Bank of India": "SBIN.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
}
INDIAN_INDICES = {"Nifty 50": "^NSEI", "Sensex": "^BSESN"}

FMT_INR = lambda x: f"₹{x/10_000_000:.2f} Cr" if x >= 10_000_000 else (
                   f"₹{x/100_000:.2f} L" if x >= 100_000 else f"₹{x:,.2f}")
FMT_NUM = lambda x: f"{x/10_000_000:.2f} Cr" if x >= 10_000_000 else (
                   f"{x/100_000:.2f} L" if x >= 100_000 else f"{x:,.0f}")

# ──────────────── Sidebar controls ─────────────────────
side = st.sidebar
dtype = side.selectbox("Data Type", ["Stocks", "Indices"])
if dtype == "Stocks":
    sel_name = side.selectbox("Stock", list(INDIAN_STOCKS))
    symbol   = INDIAN_STOCKS[sel_name]
    custom   = side.text_input("or enter NSE symbol", "")
    if custom:
        symbol   = custom if custom.endswith(".NS") else f"{custom}.NS"
        sel_name = custom.replace(".NS", "")
else:
    sel_name = side.selectbox("Index", list(INDIAN_INDICES))
    symbol   = INDIAN_INDICES[sel_name]

period_label   = side.selectbox("Period", ["1 Month", "3 Months", "6 Months",
                                           "1 Year", "2 Years"], 0)
interval_label = side.selectbox("Interval", ["1d", "1h", "15m", "5m", "1m"], 0)
chart_type     = side.selectbox("Chart", ["Candlestick", "Line", "Area"])
show_vol       = side.checkbox("Show Volume", True)
show_ma        = side.checkbox("Moving Average")
ma_period      = side.slider("MA Period", 5, 100, 20) if show_ma else 0
auto_refresh   = side.checkbox("Auto Refresh (60 s)", False)
if side.button("Refresh"): st.rerun()
side.caption(f"Last updated: {datetime.now():%Y-%m-%d %H:%M:%S}")

# ──────────────── Cached data fetch ────────────────────
@st.cache_data(ttl=300, show_spinner=False)      # 5 min cache
def load(symbol, interval):
    return fetch_data(symbol, interval)

with st.spinner(f"Loading {sel_name} …"):
    df = load(symbol, interval_label)

if df is None or df.empty:
    st.error("⚠️ Data temporarily unavailable. Try another interval or come back later.")
    st.stop()

# ──────────────── Metrics row ──────────────────────────
price = df["Close"].iloc[-1]
prev  = df["Close"].iloc[-2] if len(df) > 1 else price
delta = price - prev
pct   = delta / prev * 100 if prev else 0

market_open = 9 <= datetime.now().hour <= 15
st.markdown(
    f'<div class="market-status"><strong>{"🟢 Market Open" if market_open else "🔴 Market Closed"}</strong> | NSE</div>',
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)
c1.metric("Price", FMT_INR(price), f"₹{delta:.2f} ({pct:.2f} %)")
c2.metric("High", FMT_INR(df.High.iloc[-1]))
c2.metric("Low",  FMT_INR(df.Low.iloc[-1]))
c3.metric("Volume", FMT_NUM(df.Volume.iloc[-1]))

# ──────────────── Plotly chart ─────────────────────────
if show_vol:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_width=[.7,.3], vertical_spacing=0.04)
else:
    fig = go.Figure()

if chart_type == "Candlestick":
    fig.add_trace(
        go.Candlestick(
            x=df.index, open=df.Open, high=df.High,
            low=df.Low, close=df.Close,
            increasing_line_color="#00ff88", decreasing_line_color="#ff4b4b",
            name=sel_name),
        row=1, col=1
    )
elif chart_type == "Line":
    fig.add_trace(
        go.Scatter(x=df.index, y=df.Close, mode="lines",
                   line=dict(color="#00d4aa", width=2),
                   name=sel_name),
        row=1, col=1
    )
else:  # Area
    fig.add_trace(
        go.Scatter(x=df.index, y=df.Close, mode="lines", fill="tozeroy",
                   line=dict(color="#00d4aa"), fillcolor="rgba(0,212,170,.3)",
                   name=sel_name),
        row=1, col=1
    )

if show_ma:
    df[f"MA{ma_period}"] = df.Close.rolling(ma_period).mean()
    fig.add_trace(
        go.Scatter(x=df.index, y=df[f"MA{ma_period}"],
                   line=dict(color="#ff9500"), name=f"MA{ma_period}"),
        row=1, col=1
    )

if show_vol:
    vol_color = ["#ff4b4b" if df.Close[i] < df.Open[i] else "#00ff88"
                 for i in range(len(df))]
    fig.add_trace(
        go.Bar(x=df.index, y=df.Volume, marker_color=vol_color,
               opacity=.7, name="Volume"),
        row=2, col=1
    )

fig.update_layout(
    height=650, plot_bgcolor="#1e1e1e", paper_bgcolor="#0e1117",
    font_color="#fafafa", xaxis_rangeslider_visible=False,
    title=f"{sel_name} — {period_label} / {interval_label}"
)
st.plotly_chart(fig, use_container_width=True)

# ──────────────── Recent table ─────────────────────────
recent = df.tail(10).copy()
for col in ["Open","High","Low","Close"]:
    recent[col] = recent[col].apply(lambda x: f"₹{x:.2f}")
recent.Volume = recent.Volume.apply(FMT_NUM)
st.markdown("### Recent Data")
st.dataframe(recent, use_container_width=True)

# ──────────────── Auto-refresh ─────────────────────────
if auto_refresh:
    import time; time.sleep(60); st.experimental_rerun()
