import time
import yfinance as yf

def fetch_yahoo_or_nse(symbol: str, period="1mo", interval="1d", max_retries=3, pause=2):
    """
    Robust data loader with better error handling
    """
    # Ensure proper suffix
    if not (symbol.endswith(".NS") or symbol.startswith("^")):
        symbol += ".NS"
    
    print(f"Attempting to fetch {symbol} with period={period}, interval={interval}")
    
    # Try yfinance first
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[yfinance] Attempt {attempt}/{max_retries}")
            
            # Use Ticker.history() instead of yf.download()
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if not df.empty:
                print(f"[yfinance] Success! Got {len(df)} rows")
                return df
            else:
                print(f"[yfinance] Empty DataFrame on attempt {attempt}")
                
        except Exception as e:
            print(f"[yfinance] Error on attempt {attempt}: {str(e)}")
        
        if attempt < max_retries:
            time.sleep(pause)
    
    # If yfinance fails, try a simple fallback
    try:
        print("[fallback] Trying basic yfinance download...")
        import pandas as pd
        
        # Try a very simple download
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d")  # Force 5 days
        
        if not df.empty:
            print("[fallback] Success with 5-day data")
            return df
            
    except Exception as e:
        print(f"[fallback] Failed: {e}")
    
    print(f"[ERROR] All methods failed for {symbol}")
    return None
