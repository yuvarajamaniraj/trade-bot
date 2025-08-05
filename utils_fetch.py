import time
import yfinance as yf
from nsetools import Nse                # pip install nsetools

nse_client = Nse()

def fetch_yahoo_or_nse(symbol: str,
                       period="1mo",
                       interval="1d",
                       max_retries=3,
                       pause=2):
    """
    Robust data loader.
    • Tries yfinance up to max_retries times (single-threaded).
    • If that fails, falls back to a one-row DataFrame from NSE live quote.
    Returns a pandas DataFrame or None.
    """
    if not (symbol.endswith(".NS") or symbol.startswith("^")):
        symbol += ".NS"

    # ---------- yfinance with retries ----------
    for attempt in range(1, max_retries + 1):
        try:
            df = yf.download(
                symbol,
                period=period,
                interval=interval,
                auto_adjust=True,
                progress=False,
                threads=False        # reduces Yahoo rate-limit hits
            )
            if not df.empty:
                return df
            print(f"[yfinance] empty DF ({attempt}/{max_retries})")
        except Exception as e:
            print(f"[yfinance] {symbol} attempt {attempt}: {e}")
        time.sleep(pause)

    # ---------- fallback to NSETools ----------
    try:
        clean = symbol.replace(".NS", "")
        q = nse_client.get_quote(clean)
        if q:
            import pandas as pd, datetime as dt
            now = dt.datetime.now()
            return pd.DataFrame(
                {
                    "Open":  [q["open"]],
                    "High":  [q["dayHigh"]],
                    "Low":   [q["dayLow"]],
                    "Close": [q["lastPrice"]],
                    "Volume":[q["totalTradedVolume"]],
                },
                index=[now],
            )
    except Exception as e2:
        print(f"[nsetools] fallback failed: {e2}")

    return None
