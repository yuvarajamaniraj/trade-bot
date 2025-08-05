import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time
from datetime import datetime, timedelta

# Page configuration with dark theme
st.set_page_config(
    page_title="Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    /* Main background */
    .main .block-container {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #262730;
    }
    
    /* Metrics styling */
    div[data-testid="metric-container"] {
        background-color: #262730;
        border: 1px solid #333;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #fafafa;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Title styling */
    h1, h2, h3 {
        color: #00d4aa !important;
    }
    
    /* Text styling */
    .stMarkdown {
        color: #fafafa;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #00d4aa;
        color: #0e1117;
        border: none;
        border-radius: 0.5rem;
        font-weight: bold;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: #262730;
        color: #fafafa;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background-color: #262730;
        color: #fafafa;
        border: 1px solid #333;
    }
    
    /* Checkbox styling */
    .stCheckbox > label {
        color: #fafafa;
    }
    
    /* Dataframe styling */
    .dataframe {
        background-color: #262730 !important;
        color: #fafafa !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #262730;
        color: #fafafa;
    }
    
    /* Sidebar metric styling */
    .css-1629p8f {
        background-color: #1e1e1e;
        border-radius: 0.5rem;
        padding: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* Market status styling */
    .market-status {
        background-color: #262730;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #00d4aa;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# App title with dark theme emoji
st.title("Indian Stock Market Dashboard")
st.markdown('<div class="market-status">Real-time Indian stock prices and charts in INR</div>', unsafe_allow_html=True)

# Popular Indian stocks dictionary
INDIAN_STOCKS = {
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "State Bank of India": "SBIN.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "ITC": "ITC.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "Larsen & Toubro": "LT.NS",
    "Asian Paints": "ASIANPAINT.NS",
    "Axis Bank": "AXISBANK.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Wipro": "WIPRO.NS",
    "HCL Technologies": "HCLTECH.NS",
    "Tech Mahindra": "TECHM.NS",
    "UltraTech Cement": "ULTRACEMCO.NS",
    "Sun Pharma": "SUNPHARMA.NS"
}

# Indian indices
INDIAN_INDICES = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Bank Nifty": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Auto": "^CNXAUTO",
    "Nifty Pharma": "^CNXPHARMA",
    "Nifty FMCG": "^CNXFMCG"
}

# Function to format Indian currency
def format_inr(amount):
    """Format amount in Indian currency style with commas and ₹ symbol"""
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.2f} Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.2f} L"
    else:
        return f"₹{amount:,.2f}"

# Function to format large numbers in Indian style
def format_indian_number(num):
    """Format numbers in Indian numbering system"""
    if num >= 10000000:  # 1 crore
        return f"{num/10000000:.2f} Cr"
    elif num >= 100000:  # 1 lakh
        return f"{num/100000:.2f} L"
    else:
        return f"{num:,.0f}"

# Dark theme color palette
DARK_COLORS = {
    'bg_primary': '#0e1117',
    'bg_secondary': '#262730',
    'text_primary': '#fafafa',
    'text_secondary': '#a6a6a6',
    'accent': '#00d4aa',
    'green': '#00ff88',
    'red': '#ff4b4b',
    'chart_bg': '#1e1e1e',
    'grid': '#333333'
}

# Sidebar controls with dark theme
st.sidebar.markdown("### Chart Controls")

# Stock/Index selection
data_type = st.sidebar.selectbox("Select Data Type", ["Stocks", "Indices"])

if data_type == "Stocks":
    # Stock selection
    selected_name = st.sidebar.selectbox("Select Stock", list(INDIAN_STOCKS.keys()))
    symbol = INDIAN_STOCKS[selected_name]
    
    # Option to enter custom symbol
    custom_symbol = st.sidebar.text_input("Or enter NSE symbol (e.g., TATASTEEL.NS)", "")
    if custom_symbol:
        symbol = custom_symbol if custom_symbol.endswith('.NS') else f"{custom_symbol}.NS"
        selected_name = custom_symbol.replace('.NS', '')
else:
    # Index selection
    selected_name = st.sidebar.selectbox("Select Index", list(INDIAN_INDICES.keys()))
    symbol = INDIAN_INDICES[selected_name]

# Time period selection
period_options = {
    "1 Day": "1d",
    "5 Days": "5d", 
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "2 Years": "2y"
}
selected_period = st.sidebar.selectbox("Time Period", list(period_options.keys()), index=2)
period = period_options[selected_period]

# Interval selection
interval_options = {
    "1 Minute": "1m",
    "5 Minutes": "5m",
    "15 Minutes": "15m",
    "1 Hour": "1h",
    "1 Day": "1d"
}
selected_interval = st.sidebar.selectbox("Interval", list(interval_options.keys()), index=1)
interval = interval_options[selected_interval]

# Chart type selection
chart_type = st.sidebar.selectbox("Chart Type", ["Candlestick", "Line", "Area"])

# Technical indicators
show_volume = st.sidebar.checkbox("Show Volume", value=True)
show_ma = st.sidebar.checkbox("Show Moving Average", value=False)
ma_period = st.sidebar.slider("MA Period", 5, 100, 20) if show_ma else 20

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("Auto Refresh (60s)", value=False)

# Manual refresh button
if st.sidebar.button("Refresh Data"):
    st.rerun()

# Current time in IST
ist_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')
st.sidebar.markdown(f"**Last updated:** {ist_time}")

# Main content area
try:
    # Fetch stock data
    with st.spinner(f"Loading {selected_name} data..."):
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval=interval)
        
        if data.empty:
            st.error(f"No data found for symbol: {symbol}")
            st.stop()
    
    # Get current stock info
    info = stock.info
    current_price = data['Close'][-1]
    prev_close = data['Close'][-2] if len(data) > 1 else current_price
    price_change = current_price - prev_close
    price_change_pct = (price_change / prev_close) * 100
    
    # Market status check (Indian market hours: 9:15 AM to 3:30 PM IST)
    current_hour = datetime.now().hour
    market_status = "🟢 Market Open" if 9 <= current_hour <= 15 else "🔴 Market Closed"
    
    # Display market status with dark theme
    st.markdown(f'<div class="market-status"><strong>{market_status}</strong> | Indian Stock Exchange | NSE</div>', unsafe_allow_html=True)
    
    # Display stock info cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label=f"{selected_name} Current Price",
            value=format_inr(current_price),
            delta=f"₹{price_change:.2f} ({price_change_pct:.2f}%)"
        )
    
    with col2:
        day_high = data['High'][-1]
        day_low = data['Low'][-1]
        st.metric(
            label="Day High",
            value=format_inr(day_high)
        )
        st.metric(
            label="Day Low", 
            value=format_inr(day_low)
        )
    
    with col3:
        volume = data['Volume'][-1]
        st.metric(
            label="Volume",
            value=format_indian_number(volume)
        )
    
    with col4:
        if data_type == "Stocks":
            market_cap = info.get('marketCap', 0)
            if market_cap:
                st.metric(
                    label="Market Cap",
                    value=f"₹{market_cap / 10000000:.2f} Cr"
                )
            
            pe_ratio = info.get('trailingPE', 'N/A')
            if pe_ratio != 'N/A':
                st.metric(
                    label="P/E Ratio",
                    value=f"{pe_ratio:.2f}"
                )
        else:
            # For indices, show additional metrics
            st.metric(
                label="52W High",
                value=format_inr(info.get('fiftyTwoWeekHigh', 0)) if info.get('fiftyTwoWeekHigh') else "N/A"
            )
            st.metric(
                label="52W Low",
                value=format_inr(info.get('fiftyTwoWeekLow', 0)) if info.get('fiftyTwoWeekLow') else "N/A"
            )
    
    # Create subplots with dark theme
    if show_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=(f' ', ' '),
            row_width=[0.7, 0.3]
        )
    else:
        fig = go.Figure()
    
    # Add price chart based on type with dark theme colors
    if chart_type == "Candlestick":
        candlestick = go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name=selected_name,
            increasing_line_color=DARK_COLORS['green'],
            decreasing_line_color=DARK_COLORS['red'],
            increasing_fillcolor=DARK_COLORS['green'],
            decreasing_fillcolor=DARK_COLORS['red']
        )
        if show_volume:
            fig.add_trace(candlestick, row=1, col=1)
        else:
            fig.add_trace(candlestick)
    
    elif chart_type == "Line":
        line = go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            name=f'{selected_name} Close',
            line=dict(color=DARK_COLORS['accent'], width=3)
        )
        if show_volume:
            fig.add_trace(line, row=1, col=1)
        else:
            fig.add_trace(line)
    
    elif chart_type == "Area":
        area = go.Scatter(
            x=data.index,
            y=data['Close'],
            fill='tonexty',
            mode='lines',
            name=f'{selected_name} Close',
            line=dict(color=DARK_COLORS['accent'], width=2),
            fillcolor=f'rgba(0, 212, 170, 0.3)'
        )
        if show_volume:
            fig.add_trace(area, row=1, col=1)
        else:
            fig.add_trace(area)
    
    # Add moving average if selected
    if show_ma:
        data[f'MA{ma_period}'] = data['Close'].rolling(window=ma_period).mean()
        ma_trace = go.Scatter(
            x=data.index,
            y=data[f'MA{ma_period}'],
            mode='lines',
            name=f'MA({ma_period})',
            line=dict(color='#ff9500', width=2)
        )
        if show_volume:
            fig.add_trace(ma_trace, row=1, col=1)
        else:
            fig.add_trace(ma_trace)
    
    # Add volume chart with dark theme
    if show_volume:
        colors = [DARK_COLORS['red'] if data['Close'][i] < data['Open'][i] else DARK_COLORS['green'] 
                 for i in range(len(data))]
        
        volume = go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.7
        )
        fig.add_trace(volume, row=2, col=1)
    
    # Update layout with dark theme
    fig.update_layout(
        title=f' {selected_name} - {selected_period} Chart ({selected_interval} intervals)',
        yaxis_title='Price (₹)',
        xaxis_title='Time (IST)',
        height=700,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        plot_bgcolor=DARK_COLORS['chart_bg'],
        paper_bgcolor=DARK_COLORS['bg_primary'],
        font=dict(color=DARK_COLORS['text_primary']),
        title_font=dict(color=DARK_COLORS['accent'], size=20),
        legend=dict(
            bgcolor=DARK_COLORS['bg_secondary'],
            bordercolor=DARK_COLORS['grid'],
            borderwidth=1
        )
    )
    
    # Update grid and axes colors for dark theme
    fig.update_xaxes(
        gridcolor=DARK_COLORS['grid'],
        color=DARK_COLORS['text_primary'],
        linecolor=DARK_COLORS['grid']
    )
    fig.update_yaxes(
        gridcolor=DARK_COLORS['grid'],
        color=DARK_COLORS['text_primary'],
        linecolor=DARK_COLORS['grid']
    )
    
    if show_volume:
        fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Display additional stock information with dark theme
    if data_type == "Stocks":
        st.markdown("### Stock Information")
        
        info_col1, info_col2, info_col3 = st.columns(3)
        
        with info_col1:
            st.markdown("**Company Details:**")
            st.markdown(f"• **Company:** {info.get('longName', selected_name)}")
            st.markdown(f"• **Sector:** {info.get('sector', 'N/A')}")
            st.markdown(f"• **Industry:** {info.get('industry', 'N/A')}")
            st.markdown(f"• **Exchange:** NSE")
        
        with info_col2:
            st.markdown("**Price Metrics:**")
            st.markdown(f"• **52W High:** {format_inr(info.get('fiftyTwoWeekHigh', 0)) if info.get('fiftyTwoWeekHigh') else 'N/A'}")
            st.markdown(f"• **52W Low:** {format_inr(info.get('fiftyTwoWeekLow', 0)) if info.get('fiftyTwoWeekLow') else 'N/A'}")
            st.markdown(f"• **Previous Close:** {format_inr(info.get('previousClose', prev_close))}")
            st.markdown(f"• **Open:** {format_inr(data['Open'][-1])}")
        
        with info_col3:
            st.markdown("**Financial Ratios:**")
            st.markdown(f"• **P/E Ratio:** {info.get('trailingPE', 'N/A')}")
            st.markdown(f"• **P/B Ratio:** {info.get('priceToBook', 'N/A')}")
            st.markdown(f"• **Dividend Yield:** {info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else "N/A")
            st.markdown(f"• **Beta:** {info.get('beta', 'N/A')}")
    
    # Recent data table with dark theme
    st.markdown("### Recent Price Data")
    recent_data = data.tail(10)[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    
    # Format price columns in INR
    for col in ['Open', 'High', 'Low', 'Close']:
        recent_data[col] = recent_data[col].apply(lambda x: f"₹{x:.2f}")
    
    # Format volume
    recent_data['Volume'] = recent_data['Volume'].apply(lambda x: format_indian_number(x))
    
    # Style the dataframe for dark theme
    st.dataframe(
        recent_data,
        use_container_width=True
    )
    
    # Top Indian stocks performance (sidebar) with dark theme
    st.sidebar.markdown("### Top Stocks Today")
    
    # Fetch data for top 5 stocks
    top_stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"]
    
    for stock_symbol in top_stocks:
        try:
            stock_data = yf.Ticker(stock_symbol).history(period="2d")
            if not stock_data.empty:
                current = stock_data['Close'][-1]
                prev = stock_data['Close'][-2] if len(stock_data) > 1 else current
                change_pct = ((current - prev) / prev) * 100
                
                color = "🟢" if change_pct >= 0 else "🔴"
                st.sidebar.metric(
                    label=f"{color} {stock_symbol.replace('.NS', '')}",
                    value=f"₹{current:.2f}",
                    delta=f"{change_pct:.2f}%"
                )
        except:
            continue
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(60)
        st.rerun()

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Please check the stock symbol and try again. Make sure to use NSE symbols ending with '.NS'")

# Popular Indian stocks reference with dark theme
with st.expander("Popular Indian Stock Symbols"):
    st.markdown("""
    **Banking:** HDFCBANK.NS, ICICIBANK.NS, SBIN.NS, KOTAKBANK.NS, AXISBANK.NS
    
    **IT:** TCS.NS, INFY.NS, WIPRO.NS, HCLTECH.NS, TECHM.NS
    
    **Auto:** MARUTI.NS, TATAMOTORS.NS, M&M.NS, BAJAJ-AUTO.NS
    
    **Pharma:** SUNPHARMA.NS, DRREDDY.NS, CIPLA.NS, DIVISLAB.NS
    
    **FMCG:** ITC.NS, HINDUNILVR.NS, NESTLEIND.NS, BRITANNIA.NS
    
    **Indices:** ^NSEI (Nifty 50), ^BSESN (Sensex), ^NSEBANK (Bank Nifty)
    """)
