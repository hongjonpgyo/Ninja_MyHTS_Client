from typing import Dict, List, Optional

from PyQt6.QtWidgets import QWidget, QTableWidget
from PyQt6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, Qt
from PyQt6.QtGui import QColor, QBrush

from services.ls.ls_orderbook_engine import OrderBookEngine, OrderBookRow
from ui.widgets.ls_orderbook.ls_orderbook_renderer import OrderBookRenderer
from config.settings import ORDERBOOK_DEPTH

class LSOrderBookWidget(QWidget):
    priceClicked = pyqtSignal(float)

    COL_MIT_SELL = 0
    COL_SELL = 1
    COL_SELL_CNT = 2
    COL_SELL_QTY = 3
    COL_PRICE = 4
    COL_BUY_QTY = 5
    COL_BUY_CNT = 6
    COL_BUY = 7
    COL_MIT_BUY = 8

    # COL_MY_SELL = 2
    # COL_MY_BUY = 6

    def __init__(self, table: QTableWidget, tick_size: float, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.order_controller = None
        self.table = table
        self.tick_size = float(tick_size)
        self._dead_zone_ticks = 3

        self.symbol: Optional[str] = None
        self.center_price: Optional[float] = None
        self.last_trade_price: Optional[float] = None
        self.has_real_price = False
        self._prev_center_price: Optional[float] = None

        self._last_bids: List[Dict] = []
        self._last_asks: List[Dict] = []
        self._last_my_orders: Dict = {}
        self._protections: list[dict] = []
        self.base_price: Optional[float] = None

        self.engine = OrderBookEngine(depth=ORDERBOOK_DEPTH, tick_size=self.tick_size)
        self.renderer = OrderBookRenderer(self.table)
        self.renderer.configure_table(total_rows=ORDERBOOK_DEPTH * 2 + 1)

        self._scroll_anim: Optional[QPropertyAnimation] = None

        self.auto_center_enabled = False

        self.protection_panel = None
        self._bind_events()

    def _bind_events(self):
        # 🔥 클릭 (여기!)
        self.table.cellClicked.connect(self._on_cell_clicked)

    def set_order_controller(self, controller):
        self.order_controller = controller

    # =====================================================
    # Public API
    # =====================================================
    def set_symbol(self, symbol: str, tick_size: Optional[float] = None):
        self.symbol = symbol
        if tick_size is not None:
            self.tick_size = float(tick_size)
            self.engine.tick_size = self.tick_size

        self.center_price = None
        self._prev_center_price = None
        self._last_bids = []
        self._last_asks = []
        self._last_my_orders = {}

        self.engine.clear()
        self.renderer.render([])

    def set_protection_panel(self, panel):
        self.protection_panel = panel

    def set_protections(self, rows: list[dict]):
        """
        rows = [
          { type, price, qty }
        ]
        """
        self._protections = rows or []

        if self.engine.rows:
            self.engine.apply_protections(self._protections)
            self.renderer.render(self.engine.rows)

    def update_depth(self, bids: List[Dict], asks: List[Dict], center_price: float, my_orders: Optional[Dict] = None):
        self._last_bids = bids or []
        self._last_asks = asks or []
        if my_orders is not None:
            self._last_my_orders = my_orders

        # 🔥 핵심 방어
        if self.has_real_price:
            # ❌ ORDERBOOK center_price 무시
            pass
        else:
            # 최초 1회만 허용
            self.center_price = float(center_price)

        self._rebuild(full=True)

    def update_my_orders(self, my_orders: Dict):
        my_orders = my_orders or {}

        # 🔥 반드시 저장
        self._last_my_orders = my_orders

        # 🔥 핵심: rows에 다시 반영
        if self.engine.rows:
            for row in self.engine.rows:
                row.my_sell_cnt = 0
                row.my_buy_cnt = 0
                self.engine._apply_my_orders(row, my_orders)
            self.engine.apply_protections(self._protections)
            self.renderer.render(self.engine.rows)

    def update_ls_price(self, ls_price: float):
        self.last_trade_price = ls_price
        ls_price = float(ls_price)
        self.has_real_price = True

        # 최초 1회
        if self.center_price is None or not self.engine.rows:
            self.center_price = ls_price
            self._rebuild(full=True)
            return

        prev = self.center_price
        self._prev_center_price = prev
        self.center_price = ls_price

        # 현재가가 몇 틱 이동했는지
        tick_move = int(round((ls_price - prev) / self.tick_size))

        if tick_move == 0:
            # 같은 틱이면 중앙 표시만 갱신
            self.engine.mark_ls_price(ls_price)
            self.renderer.render(self.engine.rows)
            return

        # 너무 크게 움직이면 축 재생성
        if abs(tick_move) >= ORDERBOOK_DEPTH:
            self._rebuild(full=True)
            return

        # ✅ 핵심: rows shift → 가격들이 위/아래로 흐르는 느낌
        self._shift_rows(tick_move)

        # 🔥 여기 추가
        if tick_move > 0:
            self.renderer.nudge(dy=+6, ms=70)  # 위로 튕김
        elif tick_move < 0:
            self.renderer.nudge(dy=-6, ms=70)  # 아래로 튕김

        # depth / 내 주문 / 보호주문 재적용
        self.engine.build(
            bids=self._last_bids,
            asks=self._last_asks,
            center_price=self.center_price,  # ✅ 항상 현재가
            my_orders=self._last_my_orders,
        )

        self.engine.mark_ls_price(self.center_price)
        self.engine.apply_protections(self._protections)
        self.renderer.render(self.engine.rows)

        # 중앙 강조
        center_idx = self._find_center_index()
        if center_idx is not None:
            self.renderer.pulse_center(center_idx, ms=140)

        # update_ls_price 맨 마지막 부분
        if self.auto_center_enabled:
            self.center_price = ls_price  # 현재가 = 중심
            self._rebuild(full=True)  # 축 재정렬
            return

    def clear_base_price_visual(self):
        self.renderer.set_base_price(None)
        self.renderer.set_hover_price(None)

    def flash_execution(self, price: float, side: Optional[str] = None):
        if price is None:
            return  # 🔥 핵심 방어
        idx = self._find_row_index_by_price(price)
        if idx is None:
            return
        self.renderer.flash_row(idx, side=side, ms=180)

    # def increase_my_order(self, symbol: str, price: float, side: str, inc: int = 1):
    #     key = (symbol, float(price), side)
    #     self._my_orders[key] = self._my_orders.get(key, 0) + inc
    #
    #     # TODO: 여기서 테이블의 해당 price row 찾아서 "내 주문" 칼럼/표시 갱신
    #     # 일단은 디버그만 찍어도 OK
    #     print(f"[MY ORDER] {symbol} {side} {price} x {self._my_orders[key]}")

    # =====================================================
    # Internal
    # =====================================================
    def _rebuild(self, full: bool = True):
        if self.center_price is None:
            return

        # full rebuild: 축/마크/내주문/깊이 전부 재계산
        self.engine.build(
            bids=self._last_bids if full else self._last_bids,
            asks=self._last_asks if full else self._last_asks,
            center_price=self.center_price,
            my_orders=self._last_my_orders,
        )
        self.engine.mark_ls_price(self.center_price)
        self.engine.apply_protections(self._protections)
        self.renderer.render(self.engine.rows)

        # 기준선은 화면 중앙 쪽에 유지
        # if self.auto_center_enabled:
        #     self._scroll_to_center(animated=True)

    def _refresh_marks_only(self):
        # mark만 바꾼 후 렌더
        self.renderer.render(self.engine.rows)
        # if self.auto_center_enabled:
        #     self._scroll_to_center(animated=False)
        # 살짝 pulse
        center_idx = self._find_center_index()
        if center_idx is not None:
            self.renderer.pulse_center(center_idx, ms=120)

    def _shift_rows(self, tick_move: int):
        rows = self.engine.rows
        if not rows:
            return

        if tick_move > 0:
            for _ in range(tick_move):
                rows.pop(0)
                new_price = round(rows[-1].price - self.tick_size, 2)
                rows.append(self._make_empty_row(new_price))
        else:
            for _ in range(abs(tick_move)):
                rows.pop()
                new_price = round(rows[0].price + self.tick_size, 2)
                rows.insert(0, self._make_empty_row(new_price))

        # ✅ center는 항상 고정
        for i, r in enumerate(rows):
            r.is_center = (i == ORDERBOOK_DEPTH)
            r.is_ls_price = (round(r.price, 2) == round(self.center_price, 2))

    def _make_empty_row(self, price: float) -> OrderBookRow:
        # ✅ 네가 말한 make_empty_row "실제 구현"
        return OrderBookRow(price=round(float(price), 2))

    def _scroll_to_center(self, animated: bool = True):
        pass
        # idx = self._find_center_index()
        # if idx is None:
        #     return
        #
        # # 중앙에 유지하려면 실제 목표 스크롤 값을 계산해야 함
        # item = self.table.item(idx, self.COL_PRICE)
        # if not item:
        #     return
        #
        # sb = self.table.verticalScrollBar()
        # cur = sb.value()
        #
        # # Qt가 목표값을 계산하도록 한번 요청
        # self.table.scrollToItem(item, self.table.ScrollHint.PositionAtCenter)
        # target = sb.value()
        # sb.setValue(cur)
        #
        # if animated:
        #     self._animate_scroll(cur, target, duration=140)
        # else:
        #     sb.setValue(target)

    def _animate_scroll_by_ticks(self, tick_move: int):
        pass
        # sb = self.table.verticalScrollBar()
        # cur = sb.value()
        #
        # rh = self.table.rowHeight(0) or 18
        # step = int(rh * abs(tick_move))
        #
        # target = cur - step if tick_move > 0 else cur + step
        # target = max(sb.minimum(), min(sb.maximum(), target))
        #
        # self._animate_scroll(cur, target, duration=120)

    def _animate_scroll(self, start: int, end: int, duration: int = 140):
        # ✅ 네가 말한 _animate_scroll "실제 구현"
        sb = self.table.verticalScrollBar()
        if self._scroll_anim:
            self._scroll_anim.stop()

        self._scroll_anim = QPropertyAnimation(sb, b"value", self)
        self._scroll_anim.setDuration(duration)
        self._scroll_anim.setStartValue(start)
        self._scroll_anim.setEndValue(end)
        self._scroll_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._scroll_anim.start()

    def _find_center_index(self) -> Optional[int]:
        for i, r in enumerate(self.engine.rows):
            if r.is_center:
                return i
        return None

    def _find_row_index_by_price(self, price: float) -> Optional[int]:
        p = round(float(price), 2)
        for i, r in enumerate(self.engine.rows):
            if round(float(r.price), 2) == p:
                return i
        return None

    def _on_cell_clicked(self, row: int, col: int):
        price = self._get_price_from_row(row)
        if price is None:
            return

        qty = 1

        # =========================
        # 1️⃣ 가격 컬럼 → 보호 UX
        # =========================
        if col == self.COL_PRICE:
            # 기준가 판단 ❌
            # 그냥 가격만 전달
            self.priceClicked.emit(price)
            return

        # =========================
        # 2️⃣ 주문 컬럼 → 즉시 주문
        # =========================
        if not self.order_controller:
            return

        # 지정가 매도
        if col == self.COL_SELL:
            self.order_controller.place_limit_from_book(
                side="SELL",
                price=price,
                qty=qty,
            )
            return

        # 지정가 매수
        if col == self.COL_BUY:
            self.order_controller.place_limit_from_book(
                side="BUY",
                price=price,
                qty=qty,
            )
            return

        # 시장가 매도
        if col == self.COL_MIT_SELL:
            self.order_controller.place_market_from_book(
                side="SELL",
                qty=qty,
            )
            return

        # 시장가 매수
        if col == self.COL_MIT_BUY:
            self.order_controller.place_market_from_book(
                side="BUY",
                qty=qty,
            )
            return

    def _get_price_from_row(self, row: int) -> float | None:
        it = self.table.item(row, self.renderer.COL_PRICE)
        if not it:
            return None

        text = it.text().replace("TP", "").replace("SL", "").strip()
        try:
            return float(text.replace(",", ""))
        except ValueError:
            return None

    def clear(self):
        # 엔진 상태 초기화
        self.engine.clear()

        # 화면 비우기
        self.renderer.render([])

        # 내부 상태 초기화
        self.center_price = None
        self._prev_center_price = None
        self._last_bids = []
        self._last_asks = []
        self._last_my_orders = {}

        self.table.viewport().update()








