from collections import deque
import time

class ExecutionStrength:
    def __init__(self, window_sec=5):
        self.window_sec = window_sec
        self.trades = deque()  # (ts, side, qty)

    def add_trade(self, trade: dict):
        ts = trade.get("ts")
        side = trade.get("side")
        qty = float(trade.get("qty", 0))

        if not ts or side not in ("BUY", "SELL"):
            return

        self.trades.append((ts, side, qty))
        self._trim()

    def _trim(self):
        now = time.time()
        while self.trades and now - self.trades[0][0] > self.window_sec:
            self.trades.popleft()

    def calc(self) -> float:
        buy = sum(q for _, s, q in self.trades if s == "BUY")
        sell = sum(q for _, s, q in self.trades if s == "SELL")

        total = buy + sell
        if total == 0:
            return 0.0

        return (buy - sell) / total * 100
