# services/ls/ls_orderbook_engine.py
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class OrderBookRow:
    price: float

    ask_qty: int = 0
    bid_qty: int = 0

    ask_cnt: int = 0
    bid_cnt: int = 0

    my_sell_cnt: int = 0
    my_buy_cnt: int = 0

    is_ls_price: bool = False
    is_center: bool = False


class OrderBookEngine:
    def __init__(self, depth: int, tick_size: float):
        self.depth = depth
        self.tick_size = tick_size

        self.rows: List[OrderBookRow] = []
        self.center_price: Optional[float] = None
        self.ls_price: Optional[float] = None

    # ===============================
    # PUBLIC
    # ===============================
    def build(
        self,
        bids: List[Dict],
        asks: List[Dict],
        center_price: float,
        my_orders: Optional[Dict] = None,
    ):
        # print("[ENGINE] build called, center_price =", center_price)

        self.center_price = center_price
        self.rows = []

        price_axis = self._build_price_axis(center_price)

        bid_map = self._map_depth(bids)
        ask_map = self._map_depth(asks)

        for idx, price in enumerate(price_axis):
            row = OrderBookRow(price=price)

            # -----------------
            # ASK / BID
            # -----------------
            if price in ask_map:
                row.ask_qty = ask_map[price]["qty"]
                row.ask_cnt = ask_map[price]["cnt"]

            if price in bid_map:
                row.bid_qty = bid_map[price]["qty"]
                row.bid_cnt = bid_map[price]["cnt"]

            # -----------------
            # CENTER
            # -----------------
            if idx == self.depth:
                row.is_center = True

            # -----------------
            # MY ORDERS
            # -----------------
            if my_orders:
                self._apply_my_orders(row, my_orders)

            self.rows.append(row)

        # -----------------
        # LS 기준선
        # -----------------
        if self.ls_price is not None:
            self.mark_ls_price(self.ls_price)

    def update_ls_price(self, price: float):
        self.ls_price = price

        if not self.rows:
            self.build(
                bids=[],
                asks=[],
                center_price=price,
                my_orders=None,
            )
        else:
            self.mark_ls_price(price)

    def mark_ls_price(self, price: float):
        self.ls_price = price
        p = self._normalize_price(price)
        for r in self.rows:
            r.is_ls_price = (self._normalize_price(r.price) == p)

    def clear(self):
        self.rows.clear()
        self.center_price = None
        self.ls_price = None

    # ===============================
    # INTERNAL
    # ===============================
    def _normalize_price(self, price: float) -> float:
        """
        tick_size 기준 정규화 (float 오차 방지)
        """
        return round(round(price / self.tick_size) * self.tick_size, 6)

    def _build_price_axis(self, center_price: float) -> List[float]:
        prices: List[float] = []

        center = self._normalize_price(center_price)

        # ASK (위 → 아래)
        for i in range(self.depth, 0, -1):
            prices.append(self._normalize_price(center + i * self.tick_size))

        # CENTER
        prices.append(center)

        # BID (위 → 아래)
        for i in range(1, self.depth + 1):
            prices.append(self._normalize_price(center - i * self.tick_size))

        return prices

    def _map_depth(self, depth_list: List[Dict]) -> Dict[float, Dict]:
        out = {}
        for d in depth_list:
            price = self._normalize_price(float(d["price"]))
            out[price] = {
                "qty": int(d.get("db_all_qty", 0)),
                "cnt": int(d.get("cnt", 0)),
            }
        return out

    def _apply_my_orders(self, row: OrderBookRow, my_orders: Dict):
        """
        my_orders = {
            "SELL": {price: cnt},
            "BUY":  {price: cnt},
        }
        """
        sells = my_orders.get("SELL", {})
        buys = my_orders.get("BUY", {})

        p = self._normalize_price(row.price)

        if p in sells:
            row.my_sell_cnt = sells[p]

        if p in buys:
            row.my_buy_cnt = buys[p]
