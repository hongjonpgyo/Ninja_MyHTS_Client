# Client configuration

REST_URL = "http://127.0.0.1:9000"
WS_URL = "ws://127.0.0.1:9000/ws"
DEFAULT_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "NQ",
    "MNQ",
]
YAHOO_SYMBOL_MAP = {
    "ESZ25": "ES=F",      # S&P500 선물
    "NQZ25": "NQ=F",      # 나스닥 선물
    "GCZ25": "GC=F",      # 금 선물
    "UROZ25": "EURUSD=X", # 유로/달러
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "NQ": "NQ=F",
    "MNQ": "MNQ=F",
}
BINANCE_SYMBOLS = {
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT",
}

# 선물/지수쪽은 일단 분리 (차후 source registry로 확장 가능)
FUTURES_SYMBOLS = {"NQ", "MNQ"}

MIT_SELL_COL = 0
LMT_SELL_COL = 1
MIT_BUY_COL = 8
LMT_BUY_COL = 7
