# app.py  ── fully self-contained dark-mode dashboard
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import datetime
import time
from utils_fetch import fetch_yahoo_or_nse      # helper you already added

# ───────────────── Streamlit page config ─────────────────
st.set_page_config("Indian Stock Dashboard", "📈", layout="wide")

# ──────────────── INLINE Dark-theme CSS ──────────────────
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
.stCheckbox>label{color:#fafafa}.dataframe{background:#262730!important;color:#fafafa!important}
.streamlit-expanderHeader{background:#262730;color:#fafafa}
.css-1629p8f{background:#1e1e1e;border-radius:.5rem;padding:.5rem;margin-bottom:.5rem}
.market-status{background:#262730;padding:1rem;border-radius:.5rem;border-left:4px solid #00d4aa;margin-bottom:1rem}
</style>
""", unsafe_allow_html=True)

# ──────────────── Dashboard Header ───────────────────────
st.title("Indian Stock Market Dashboard")
st.markdown('<div class="market-status">Real-time Indian stock prices in INR</div>', unsafe_allow_html=True)

# ──────────────── Symbol dictionaries ────────────────────
INDIAN_STOCKS = {
    "Reliance Industries": "RELIANCE.NS", "TCS": "TCS.NS", "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS", "ICICI Bank": "ICICIBANK.NS", "State Bank of India": "SBIN.NS",
    "Bajaj Finance": "BAJFINANCE.NS", "Bharti Airtel": "BHARTIARTL.NS", "ITC": "ITC.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS", "Larsen & Toubro": "LT.NS",
    "Asian Paints": "ASIANPAINT.NS", "Axis Bank": "AXISBANK.NS", "Maruti Suzuki": "MARUTI.NS",
    "Tata Motors": "TATAMOTORS.NS", "Wipro": "WIPRO.NS", "HCL Technologies": "HCLTECH.NS",
    "Tech Mahindra": "TECHM.NS", "UltraTech Cement": "ULTRACEMCO.NS", "Sun Pharma": "SUNPHARMA.NS"
}
INDIAN_INDICES = {"Nifty 50": "^NSEI", "Sensex": "^BSESN", "Bank Nifty": "^NSEBANK"}

# ─────────────── Utility formatters ──────────────────────
fmt_inr = lambda x: f"₹{x/10_000_000:.2f} Cr" if x>=10_000_000 else (f"₹{x/100_000:.2f} L" if x>=100_000 else f"₹{x:,.2f}")
fmt_num = lambda x: f"{x/10_000_000:.2f} Cr" if x>=10_000_000 else (f"{x/100_000:.2f} L" if x>=100_000 else f"{x:,.0f}")

# ──────────────── Sidebar controls ───────────────────────
side = st.sidebar
dtype = side.selectbox("Data Type", ["Stocks","Indices"])
if dtype=="Stocks":
    sel = side.selectbox("Stock", list(INDIAN_STOCKS))
    symbol = INDIAN_STOCKS[sel]
    custom = side.text_input("or enter NSE symbol", "")
    if custom:
        symbol = custom if custom.endswith(".NS") else f"{custom}.NS"
        sel = custom.replace(".NS","")
else:
    sel = side.selectbox("Index", list(INDIAN_INDICES))
    symbol = INDIAN_INDICES[sel]

period = {"1 Day":"1d","5 Days":"5d","1 Month":"1mo","3 Months":"3mo","6 Months":"6mo","1 Year":"1y"}[side.selectbox("Period",["1 Day","5 Days","1 Month","3 Months","6 Months","1 Year"],2)]
interval = {"1m":"1m","5m":"5m","15m":"15m","1h":"1h","1d":"1d"}[side.selectbox("Interval",["1m","5m","15m","1h","1d"],1)]
ctype = side.selectbox("Chart Type",["Candlestick","Line","Area"])
show_vol = side.checkbox("Show Volume",True)
show_ma = side.checkbox("Show Moving Average")
ma_n = side.slider("MA Period",5,100,20) if show_ma else 0
auto = side.checkbox("Auto Refresh (60 s)")

if side.button("Refresh"): st.rerun()
side.caption(f"Last updated: {datetime.now():%Y-%m-%d %H:%M:%S}")

# ──────────────── Data fetch ─────────────────────────────
with st.spinner(f"Loading {sel} …"):
    df = fetch_yahoo_or_nse(symbol, period, interval)
if df is None:
    st.error("Unable to fetch data. Try another symbol or time.")
    st.stop()

info = yf.Ticker(symbol).info
price, prev = df.Close.iloc[-1], df.Close.iloc[-2] if len(df)>1 else df.Close.iloc[-1]
chg, pct = price-prev, (price-prev)/prev*100 if prev else 0

# ──────────────── Market status ──────────────────────────
now_h = datetime.now().hour
open_flag = 9 <= now_h <= 15
st.markdown(f'<div class="market-status"><strong>{"🟢 Market Open" if open_flag else "🔴 Market Closed"}</strong> | NSE</div>', unsafe_allow_html=True)

# ──────────────── KPI row ───────────────────────────────
c1,c2,c3,c4 = st.columns(4)
c1.metric("Price", fmt_inr(price), f"₹{chg:.2f} ({pct:.2f} %)")
c2.metric("High", fmt_inr(df.High.iloc[-1])); c2.metric("Low",fmt_inr(df.Low.iloc[-1]))
c3.metric("Volume", fmt_num(df.Volume.iloc[-1]))
if dtype=="Stocks" and info.get("marketCap"): c4.metric("Mkt Cap", fmt_inr(info["marketCap"]))

# ──────────────── Plotly chart ───────────────────────────
if show_vol:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[.7,.3])
else:
    fig = go.Figure()

if ctype=="Candlestick":
    fig.add_trace(go.Candlestick(x=df.index,open=df.Open,high=df.High,low=df.Low,close=df.Close,
                                 increasing_line_color="#00ff88",decreasing_line_color="#ff4b4b"), row=1,col=1)
elif ctype=="Line":
    fig.add_trace(go.Scatter(x=df.index,y=df.Close,mode="lines",line=dict(color="#00d4aa",width=2)), row=1,col=1)
else:
    fig.add_trace(go.Scatter(x=df.index,y=df.Close,mode="lines",fill="tozeroy",
                             line=dict(color="#00d4aa"),fillcolor="rgba(0,212,170,.3)"), row=1,col=1)

if show_ma:
    df[f"MA{ma_n}"] = df.Close.rolling(ma_n).mean()
    fig.add_trace(go.Scatter(x=df.index,y=df[f"MA{ma_n}"],line=dict(color="#ff9500"),name=f"MA{ma_n}"), row=1,col=1)

if show_vol:
    colors = ["#ff4b4b" if df.Close[i]<df.Open[i] else "#00ff88" for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index,y=df.Volume,marker_color=colors,opacity=.7,name="Volume"), row=2,col=1)

fig.update_layout(height=700,plot_bgcolor="#1e1e1e",paper_bgcolor="#0e1117",font_color="#fafafa",
                  xaxis_rangeslider_visible=False,title=f"{sel} — {period}/{interval}")
st.plotly_chart(fig,use_container_width=True)

# ──────────────── Recent table ───────────────────────────
recent = df.tail(10).copy()
for col in ["Open","High","Low","Close"]: recent[col]=recent[col].apply(lambda x:f"₹{x:.2f}")
recent.Volume = recent.Volume.apply(fmt_num)
st.markdown("### Recent Data")
st.dataframe(recent,use_container_width=True)

# ──────────────── Auto-refresh ───────────────────────────
if auto:
    time.sleep(60); st.experimental_rerun()
