"""
utils_fetch.py
────────────────────────────────────────────
Daily candles  → Stooq   (free, no key)  
Intraday       → Alpha Vantage (only if ALPHAVANTAGE_KEY is set)
"""

import os, pandas as pd, requests
from pandas_datareader import data as pdr

AV_KEY = os.getenv("ALPHAVANTAGE_KEY", "")       # optional

# ───────────────────────── helpers ─────────────────────────
def _symbol_to_stooq(symbol: str) -> str:
    """
    Convert Yahoo/NSE style codes to Stooq codes.
    • Shares:  RELIANCE.NS → RELIANCE
    • Indices: ^NSEI       → nsei.in
    """
    if symbol.startswith("^"):                    # index
        return symbol.lstrip("^").lower() + ".in"
    return symbol.replace(".NS", "")

# ───────────────────────── Stooq reader ────────────────────
def _from_stooq(symbol: str, start="2020-01-01"):
    code = _symbol_to_stooq(symbol)
    df   = pdr.DataReader(code, "stooq", start)
    if df.empty:
        return None
    df.sort_index(inplace=True)
    df.index = df.index.tz_localize("UTC").tz_convert("Asia/Kolkata")
    df.rename(columns=str.title, inplace=True)          # Open,High,…
    return df

# ─────────────────────── Alpha Vantage ─────────────────────
def _from_av(symbol: str, interval="5min", size="compact"):
    if not AV_KEY:
        return None
    code = symbol.replace(".NS", "") + ".BSE"           # AV wants .BSE
    url  = (
        "https://www.alphavantage.co/query"
        f"?function=TIME_SERIES_INTRADAY&symbol={code}"
        f"&interval={interval}&outputsize={size}&apikey={AV_KEY}&datatype=csv"
    )
    try:
        csv = requests.get(url, timeout=10).text
        df  = pd.read_csv(pd.compat.StringIO(csv))
        if df.empty:
            return None
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        df.index = df.index.tz_localize("UTC").tz_convert("Asia/Kolkata")
        df.rename(
            columns=dict(
                open="Open", high="High", low="Low", close="Close", volume="Volume"
            ),
            inplace=True,
        )
        df.sort_index(inplace=True)
        return df
    except Exception as e:
        print("[Alpha Vantage]", e)
        return None

# ───────────────────────── main API ────────────────────────
def fetch_data(symbol: str, interval_label: str):
    """
    Returns a DataFrame with OHLCV in IST tz or None.
    """
    intraday = interval_label in {"1m", "5m", "15m", "1h"}
    if intraday:
        av_int = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "60min"}[
            interval_label
        ]
        df = _from_av(symbol, av_int)
        if df is not None:
            return df
    return _from_stooq(symbol)
