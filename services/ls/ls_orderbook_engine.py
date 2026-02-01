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
        다양한 형태를 허용:
        1) { "type": "TP|SL", "price": 26850.0, "cnt": 1 }
        2) DB row 형태:
           { "protection_type": "...", "trigger_price": ..., "qty": ..., "close_side": "BUY|SELL", ... }
           { "type": "...", "trigger_price": ..., "qty": ... } 등
        """
        # if not self.rows:
        #     return

        # ✅ 항상 초기화 (중복/잔상 방지)
        for r in self.rows:
            r.is_tp = False
            r.is_sl = False
            r.my_mit_sell = 0
            r.my_mit_buy = 0

        tp_map: Dict[float, int] = {}
        sl_map: Dict[float, int] = {}
        mit_sell_map: Dict[float, int] = {}
        mit_buy_map: Dict[float, int] = {}

        for raw in protections or []:
            ptype = (
                    raw.get("type")
                    or raw.get("protection_type")
                    or raw.get("kind")
                    or ""
            )
            ptype = str(ptype).upper().strip()

            # ✅ TP/SL 정규화 (여기 아주 중요)
            if ptype in ("TAKE_PROFIT", "TP_PROFIT", "PROFIT", "익절"):
                ptype = "TP"
            if ptype in ("STOP_LOSS", "SL_LOSS", "LOSS", "손절"):
                ptype = "SL"

            # 가격 키 후보들
            price_val = (
                raw.get("price")
                if raw.get("price") is not None
                else raw.get("trigger_price")
                if raw.get("trigger_price") is not None
                else raw.get("request_price")
            )
            if price_val in (None, "", " "):
                continue

            try:
                price = self.normalize_price(float(price_val))
            except Exception:
                continue

            # 수량/건수 후보들 (없으면 1건)
            cnt_val = (
                raw.get("cnt")
                if raw.get("cnt") is not None
                else raw.get("qty")
                if raw.get("qty") is not None
                else raw.get("count")
            )
            try:
                cnt = int(cnt_val) if cnt_val not in (None, "", " ") else 1
            except Exception:
                cnt = 1

            # ✅ TP/SL 라인 플래그용 맵
            if ptype == "TP":
                tp_map[price] = tp_map.get(price, 0) + cnt
            elif ptype == "SL":
                sl_map[price] = sl_map.get(price, 0) + cnt

            # ✅ MIT 칼럼(청산 방향) 결정
            close_side = raw.get("close_side") or raw.get("side") or raw.get("exit_side")
            close_side = str(close_side).upper().strip() if close_side else ""

            if close_side in ("SELL", "S"):
                mit_sell_map[price] = mit_sell_map.get(price, 0) + cnt
            elif close_side in ("BUY", "B"):
                mit_buy_map[price] = mit_buy_map.get(price, 0) + cnt
            else:
                # close_side 없으면 fallback (기존 네 정책 유지)
                # TP → SELL MIT, SL → BUY MIT (원하면 여기 바꿔도 됨)
                if ptype == "TP":
                    mit_sell_map[price] = mit_sell_map.get(price, 0) + cnt
                elif ptype == "SL":
                    mit_buy_map[price] = mit_buy_map.get(price, 0) + cnt

        for r in self.rows:
            p = self.normalize_price(r.price)

            r.is_tp = p in tp_map
            r.is_sl = p in sl_map

            r.my_mit_sell = mit_sell_map.get(p, 0)
            r.my_mit_buy = mit_buy_map.get(p, 0)

        print("[MIT MAP SIZE]", sum(r.my_mit_buy + r.my_mit_sell for r in self.rows))

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
