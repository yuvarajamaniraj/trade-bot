"""
utils_fetch.py
———————————————
Single, reliable data-loader for Streamlit Cloud.

• Uses Stooq (free, no key, not geo-blocked) for daily OHLCV.
• Optional Alpha Vantage intraday if you add ALPHAVANTAGE_KEY
  in Streamlit → Settings → Secrets.
"""

import os, datetime as dt
import pandas as pd
import requests
from pandas_datareader import data as pdr

AV_KEY = os.getenv("ALPHAVANTAGE_KEY", "")        # optional

# ────────────────────────────────────────────
def _from_stooq(symbol: str, start="2020-01-01"):
    stooq_symbol = symbol.replace(".NS", "").lower() + ".in"
    df = pdr.DataReader(stooq_symbol, "stooq", start)
    if df.empty:
        return None
    df.sort_index(inplace=True)
    df.index = (
        df.index
        .tz_localize("UTC")
        .tz_convert("Asia/Kolkata")
    )
    df.rename(columns=str.title, inplace=True)
    return df

# ────────────────────────────────────────────
def _from_av(symbol: str, interval="5min", output="compact"):
    if not AV_KEY:
        return None

    ns = symbol.replace(".NS", "")
    url = (
        f"https://www.alphavantage.co/query?"
        f"function=TIME_SERIES_INTRADAY&symbol={ns}.BSE"
        f"&interval={interval}&outputsize={output}&apikey={AV_KEY}&datatype=csv"
    )
    try:
        csv = requests.get(url, timeout=10).text
        df = pd.read_csv(pd.compat.StringIO(csv))
        if df.empty:
            return None
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        df.index = df.index.tz_localize("UTC").tz_convert("Asia/Kolkata")
        df.rename(
            columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            },
            inplace=True,
        )
        df.sort_index(inplace=True)
        return df
    except Exception as e:
        print("[Alpha Vantage]", e)
        return None

# ────────────────────────────────────────────
def fetch_data(symbol: str, interval_label: str):
    """
    Returns a pandas DataFrame with standard OHLCV columns or None.
    """
    intraday = interval_label in {"1m", "5m", "15m", "1h"}
    if intraday:
        av_interval = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "1h": "60min",
        }.get(interval_label, "5min")
        df = _from_av(symbol, av_interval)
        if df is not None:
            return df

    return _from_stooq(symbol)
