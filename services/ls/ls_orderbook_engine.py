from dataclasses import dataclass
from typing import Dict, List, Optional


# =====================================================
# Row Model
# =====================================================
@dataclass
class OrderBookRow:
    price: float

    # 거래소 호가
    ask_qty: int = 0
    bid_qty: int = 0
    ask_cnt: int = 0
    bid_cnt: int = 0

    # 내 지정가 주문
    my_sell_cnt: int = 0
    my_buy_cnt: int = 0

    # 🔥 MIT / 보호주문
    my_mit_sell: int = 0
    my_mit_buy: int = 0

    # 상태 플래그
    is_ls_price: bool = False
    is_center: bool = False
    is_tp: bool = False
    is_sl: bool = False


# =====================================================
# Engine
# =====================================================
class OrderBookEngine:
    def __init__(self, depth: int, tick_size: float):
        self.depth = depth
        self.tick_size = tick_size

        self.rows: List[OrderBookRow] = []
        self.center_price: Optional[float] = None
        self.ls_price: Optional[float] = None

    # =================================================
    # PUBLIC
    # =================================================
    def build(
        self,
        bids: List[Dict],
        asks: List[Dict],
        center_price: float,
        my_orders: Optional[Dict] = None,
    ):
        """
        호가 스냅샷 기반 전체 재구성
        (MIT / TP / SL 은 여기서 처리하지 않음)
        """
        self.center_price = center_price
        self.rows.clear()

        price_axis = self._build_price_axis(center_price)
        bid_map = self._map_depth(bids)
        ask_map = self._map_depth(asks)

        for idx, price in enumerate(price_axis):
            row = OrderBookRow(price=price)

            # 거래소 호가
            if price in ask_map:
                row.ask_qty = ask_map[price]["qty"]
                row.ask_cnt = ask_map[price]["cnt"]

            if price in bid_map:
                row.bid_qty = bid_map[price]["qty"]
                row.bid_cnt = bid_map[price]["cnt"]

            # 기준선
            row.is_center = (idx == self.depth)

            # 내 지정가 주문
            if my_orders:
                self._apply_my_orders(row, my_orders)

            self.rows.append(row)

        # 현재가 표시
        if self.ls_price is not None:
            self.mark_ls_price(self.ls_price)

    def update_ls_price(self, price: float):
        """
        실시간 체결가 업데이트
        """
        self.ls_price = price

        if not self.rows:
            self.build(bids=[], asks=[], center_price=price)
        else:
            self.mark_ls_price(price)

    def mark_ls_price(self, price: float):
        p = self.normalize_price(price)
        for r in self.rows:
            r.is_ls_price = (self.normalize_price(r.price) == p)

    def clear(self):
        self.rows.clear()
        self.center_price = None
        self.ls_price = None

    # =================================================
    # MIT / PROTECTIONS
    # =================================================
    def apply_protections(self, protections: List[Dict]):
        """
        protections = [
          { "type": "TP", "price": 26850.0, "cnt": 1 },
          { "type": "SL", "price": 26600.0, "cnt": 2 },
        ]
        """
        if not self.rows:
            return

        # 🔥 항상 초기화 (중복 방지)
        for r in self.rows:
            r.is_tp = False
            r.is_sl = False
            r.my_mit_sell = 0
            r.my_mit_buy = 0

        tp_map: Dict[float, int] = {}
        sl_map: Dict[float, int] = {}

        for p in protections:
            price = self.normalize_price(float(p["price"]))
            cnt = int(p.get("cnt", 1))

            if p["type"] == "TP":
                tp_map[price] = tp_map.get(price, 0) + cnt
            elif p["type"] == "SL":
                sl_map[price] = sl_map.get(price, 0) + cnt

        for r in self.rows:
            p = self.normalize_price(r.price)

            r.is_tp = p in tp_map
            r.is_sl = p in sl_map

            # TP → 매도 MIT / SL → 매수 MIT
            r.my_mit_sell = tp_map.get(p, 0)
            r.my_mit_buy = sl_map.get(p, 0)

    # =================================================
    # INTERNAL
    # =================================================
    def normalize_price(self, price: float) -> float:
        """
        tick_size 기준 정규화
        """
        return round(round(price / self.tick_size) * self.tick_size, 6)

    def _build_price_axis(self, center_price: float) -> List[float]:
        center = self.normalize_price(center_price)
        prices: List[float] = []

        # ASK (위)
        for i in range(self.depth, 0, -1):
            prices.append(self.normalize_price(center + i * self.tick_size))

        prices.append(center)

        # BID (아래)
        for i in range(1, self.depth + 1):
            prices.append(self.normalize_price(center - i * self.tick_size))

        return prices

    def _map_depth(self, depth_list: List[Dict]) -> Dict[float, Dict]:
        out: Dict[float, Dict] = {}

        for d in depth_list:
            price = self.normalize_price(float(d["price"]))
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
        p = self.normalize_price(row.price)

        row.my_sell_cnt = my_orders.get("SELL", {}).get(p, 0)
        row.my_buy_cnt = my_orders.get("BUY", {}).get(p, 0)
