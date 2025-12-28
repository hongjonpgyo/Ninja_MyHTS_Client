import yfinance as yf

class YahooPriceFeeder:
    def __init__(self, feed_manager, symbol_map: dict):
        self.feed = feed_manager
        self.symbol_map = symbol_map  # local_symbol -> yahoo_symbol

    def poll(self):
        yahoo_symbols = list(self.symbol_map.values())
        # print(yahoo_symbols)
        if not yahoo_symbols:
            return

        df = None

        # 1분봉이 비는 경우가 있어서 interval fallback
        for interval in ("1m", "5m", "15m"):
            try:
                df = yf.download(
                    tickers=yahoo_symbols,
                    period="1d",
                    interval=interval,
                    group_by="ticker",
                    threads=False,   # 안정성 우선
                    progress=False,
                    auto_adjust=False,
                )
                if df is not None and not df.empty:
                    break
            except Exception as e:
                print(f"[YahooFeed] download error interval={interval}:", e)
                df = None

        if df is None or df.empty:
            print("[YahooFeed] empty dataframe")
            return

        # 단일/멀티 심볼 DataFrame 모두 처리
        for local_symbol, ysym in self.symbol_map.items():
            try:
                last_price = None

                # 멀티심볼이면 df[ysym]["Close"], 단일이면 df["Close"]
                if isinstance(df.columns, type(df.columns)) and ("Close" in df.columns) and ysym not in df.columns:
                    # 단일 심볼 케이스
                    close_series = df["Close"].dropna()
                else:
                    # 멀티 심볼 케이스 (group_by="ticker")
                    close_series = df[ysym]["Close"].dropna()

                if not close_series.empty:
                    last_price = float(close_series.iloc[-1])

                if last_price is None:
                    # 마지막 보험: Ticker.history로 재시도
                    t = yf.Ticker(ysym)
                    hist = t.history(period="1d", interval="1m")
                    hist_close = hist["Close"].dropna() if "Close" in hist else None
                    if hist_close is not None and not hist_close.empty:
                        last_price = float(hist_close.iloc[-1])

                if last_price is not None:
                    # ✅ 여기서 PriceController로 흘러가게 됨
                    # print(local_symbol, last_price)
                    self.feed.emit_price(local_symbol, last_price)

            except Exception as e:
                print(f"[YahooFeed] {local_symbol}/{ysym} parse error:", e)
