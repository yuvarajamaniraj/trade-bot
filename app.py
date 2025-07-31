import dash
from dash import dcc, html
from dash.dependencies import Output, Input, State
import plotly.graph_objs as go
import requests
from datetime import datetime
import time, hmac, hashlib, json
import os

# --- Parameters and Theme ---
UPDATE_INTERVAL = 10 * 1000  # ms
WINDOW_SIZE = 80
BTCINR_API = "https://api.coindcx.com/exchange/ticker"
TARGET_THRESHOLD = 0.10

BG_COLOR = '#18181a'
ACCENT_COLOR = '#66c2ff'
AXIS_TEXT_COLOR = '#ccc'
TABLE_HEADER_BG = '#23232b'
TABLE_ROW_BG = '#1a1a22'
BUTTON_BUY_BG = '#3fd283'
BUTTON_SELL_BG = '#ff7675'

# --- Read CoinDCX credentials from environment for security on Render ---
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")

historic_times = []
historic_prices = []
trade_init_value = None
trade_history = []

def fetch_btcinr_price():
    try:
        resp = requests.get(BTCINR_API, timeout=2)
        for ticker in resp.json():
            if ticker.get('market', '').upper() == "BTCINR":
                return float(ticker['last_price'])
    except Exception as e:
        print(f"API fetch error: {e}")
        return None

def indian_num_fmt(val):
    if val is None:
        return ""
    n = int(val)
    s = str(n)
    if len(s) <= 3:
        return s
    last3 = s[-3:]
    rest = s[:-3]
    out = ''
    while len(rest) > 2:
        out = ',' + rest[-2:] + out
        rest = rest[:-2]
    if rest:
        out = rest + out
    return out + ',' + last3

def place_market_order(side, market, quantity):
    url = "https://api.coindcx.com/exchange/v1/orders/create"
    body = {
        "side": side,
        "order_type": "market_order",
        "market": market,
        "total_quantity": quantity,
        "timestamp": int(time.time() * 1000)
    }
    payload = json.dumps(body, separators=(',', ':'))
    signature = hmac.new(
        (API_SECRET or '').encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': API_KEY or '',
        'X-AUTH-SIGNATURE': signature
    }
    try:
        resp = requests.post(url, headers=headers, data=payload)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

app = dash.Dash(__name__)
server = app.server  # For Gunicorn/Render

app.layout = html.Div(
    style={
        'display': 'flex',
        'flexDirection': 'column',
        'height': '100vh',
        'backgroundColor': BG_COLOR,
        'color': AXIS_TEXT_COLOR,
        'padding': '16px',
        'margin': 0,
        'overflow': 'hidden',
        'fontFamily': 'Roboto,Arial,sans-serif',
    },
    children=[
        html.Div(
            dcc.Graph(
                id='live-btc-graph',
                config={'displayModeBar': False},
                style={
                    'backgroundColor': BG_COLOR,
                    'border': 'none',
                    'padding': 0,
                    'margin': 0,
                    'boxShadow': '0 0 16px #0006',
                    'width': '100%',
                    'height': '100%'
                }
            ),
            style={'marginBottom': '12px', 'flex': '0 0 auto'}
        ),
        html.Div([
            html.Button(
                "Buy 0.001 BTC",
                id='buy-btn',
                n_clicks=0,
                style={
                    'backgroundColor': BUTTON_BUY_BG,
                    'color': '#18181a',
                    'border': 'none',
                    'padding': '10px 24px',
                    'marginRight': '14px',
                    'borderRadius': '6px',
                    'fontWeight': 'bold',
                    'fontSize': '1em',
                    'cursor': 'pointer',
                    'boxShadow': '0 0 6px #263'
                }
            ),
            html.Button(
                "Sell 0.001 BTC",
                id='sell-btn',
                n_clicks=0,
                style={
                    'backgroundColor': BUTTON_SELL_BG,
                    'color': '#18181a',
                    'border': 'none',
                    'padding': '10px 24px',
                    'borderRadius': '6px',
                    'fontWeight': 'bold',
                    'fontSize': '1em',
                    'cursor': 'pointer',
                    'boxShadow': '0 0 6px #833'
                }
            )
        ], style={'textAlign': 'center', 'marginTop': '8px', 'marginBottom': '0', 'flex': '0 0 auto'}),
        dcc.Interval(id='interval-update', interval=UPDATE_INTERVAL, n_intervals=0),
        html.Div(
