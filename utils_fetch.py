import time
import yfinance as yf
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def fetch_yahoo_or_nse(symbol: str, period="1mo", interval="1d", max_retries=5, pause=3):
    """
    Ultra-robust data fetcher with multiple fallback strategies
    """
    if not (symbol.endswith(".NS") or symbol.startswith("^")):
        symbol += ".NS"
    
    print(f"[DEBUG] Fetching {symbol} with period={period}, interval={interval}")
    
    # Strategy 1: Direct yfinance with custom session
    for attempt in range(1, max_retries + 1):
        try:
            # Create custom session with retries
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # Update headers to avoid blocking
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            ticker = yf.Ticker(symbol, session=session)
            df = ticker.history(period=period, interval=interval)
            
            if not df.empty:
                print(f"[SUCCESS] Got {len(df)} rows for {symbol}")
                return df
            else:
                print(f"[EMPTY] Attempt {attempt}: Empty DataFrame")
                
        except Exception as e:
            print(f"[ERROR] Attempt {attempt}: {str(e)}")
        
        if attempt < max_retries:
            print(f"[WAIT] Sleeping {pause} seconds...")
            time.sleep(pause)
    
    # Strategy 2: Try different periods/intervals
    fallback_configs = [
        {"period": "5d", "interval": "1d"},
        {"period": "1mo", "interval": "1d"},
        {"period": "3mo", "interval": "1wk"},
    ]
    
    for config in fallback_configs:
        try:
            print(f"[FALLBACK] Trying {config}")
            ticker = yf.Ticker(symbol)
            df = ticker.history(**config)
            
            if not df.empty:
                print(f"[FALLBACK SUCCESS] Got data with {config}")
                return df
                
        except Exception as e:
            print(f"[FALLBACK ERROR] {config}: {str(e)}")
        
        time.sleep(2)
    
    # Strategy 3: Use yf.download instead
    try:
        print(f"[DOWNLOAD] Trying yf.download method")
        df = yf.download(symbol, period="1mo", interval="1d", progress=False)
        
        if not df.empty:
            print(f"[DOWNLOAD SUCCESS] Got {len(df)} rows")
            return df
            
    except Exception as e:
        print(f"[DOWNLOAD ERROR] {str(e)}")
    
    print(f"[FINAL ERROR] All strategies failed for {symbol}")
    return None
