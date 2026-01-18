# Client configuration

# REST_URL = "http://127.0.0.1:9000"
WS_URL = "ws://127.0.0.1:9000/ws"
LS_BASE_URL = "http://127.0.0.1:9001"

ORDERBOOK_DEPTH = 100
DEFAULT_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
]
# YAHOO_SYMBOL_MAP = {
#     "ESZ25": "ES=F",      # S&P500 선물
#     "NQZ25": "NQ=F",      # 나스닥 선물
#     "GCZ25": "GC=F",      # 금 선물
#     "UROZ25": "EURUSD=X", # 유로/달러
#     "BTCUSDT": "BTC-USD",
#     "ETHUSDT": "ETH-USD",
#     "NQ": "NQ=F",
#     "MNQ": "MNQ=F",
# }
BINANCE_SYMBOLS = {
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT",
}

# 선물/지수쪽은 일단 분리 (차후 source registry로 확장 가능)
FUTURES_SYMBOLS = {"NQ", "MNQ"}

MIT_SELL_COL = 0   # 좌측 MIT (청산용 / 매도)
LMT_SELL_COL = 1   # 좌측 매도 (진입 SELL)
COL_SELL_CNT = 2   # 좌측 내 주문 건수

PRICE_COL    = 4   # 가격 (중앙)

COL_BUY_CNT  = 6   # 우측 내 주문 건수
LMT_BUY_COL  = 7   # 우측 매수 (진입 BUY)
MIT_BUY_COL  = 8   # 우측 MIT (청산용 / 매수)

LS_SYMBOL_KR_MAP = {
    # H-Share / China
    "HSI": "항셍",
    "HCEI": "항셍중국",
    "HCHH": "중국국채",
    "CUS": "위안",

    # US
    "ES": "S&P",
    "NQ": "나스닥",
    "YM": "다우",

    # FX
    "EUR": "유로",
    "JPY": "엔",
}

