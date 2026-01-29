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

        self.symbol: Optional[str] = None
        self.center_price: Optional[float] = None
        self._prev_center_price: Optional[float] = None

        self._last_bids: List[Dict] = []
        self._last_asks: List[Dict] = []
        self._last_my_orders: Dict = {}
        self._protections: list[dict] = []

        self.table.cellClicked.connect(self.on_orderbook_click)

        self.engine = OrderBookEngine(depth=ORDERBOOK_DEPTH, tick_size=self.tick_size)
        self.renderer = OrderBookRenderer(self.table)
        self.renderer.configure_table(total_rows=ORDERBOOK_DEPTH * 2 + 1)

        self._scroll_anim: Optional[QPropertyAnimation] = None

        self.auto_center_enabled = False

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

        self._prev_center_price = self.center_price
        self.center_price = float(center_price)

        # depth 업데이트는 일단 build로 재생성 OK (깊이 데이터가 바뀌기 때문)
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

            self.renderer.render(self.engine.rows)

    def update_ls_price(self, ls_price: float):
        """
        ✅ '이동감' 핵심:
        - build로 매번 갈아끼우지 말고 rows를 shift 해서 위/아래로 밀어준다
        """
        ls_price = float(ls_price)

        if self.center_price is None or not self.engine.rows:
            # 최초 1회는 build
            self._prev_center_price = self.center_price
            self.center_price = ls_price
            self._rebuild(full=True)
            return

        prev = float(self.center_price)
        self._prev_center_price = prev
        self.center_price = ls_price

        # 몇 틱 움직였는지
        tick_move = int(round((ls_price - prev) / self.tick_size))

        if tick_move == 0:
            # 같은 틱이면 기준선만 갱신 + 가벼운 pulse
            self.engine.mark_ls_price(ls_price)
            self._refresh_marks_only()
            return

        # 너무 많이 점프하면(예: 10틱 이상) shift보다 build가 안정적
        if abs(tick_move) > ORDERBOOK_DEPTH:
            self._rebuild(full=True)
            return

        # ✅ 이동감: shift
        self._shift_rows(tick_move)

        # shift 후 depth/my_order 반영은 "가볍게" 재적용(축은 유지)
        self.engine.build(
            bids=self._last_bids,
            asks=self._last_asks,
            center_price=self.center_price,
            my_orders=self._last_my_orders,
        )
        self.engine.mark_ls_price(self.center_price)
        self.engine.apply_protections(self._protections)
        self.renderer.render(self.engine.rows)

        # 방향감 스크롤(아주 살짝)
        self._animate_scroll_by_ticks(tick_move)

        # center pulse
        center_idx = self._find_center_index()
        if center_idx is not None:
            self.renderer.pulse_center(center_idx, ms=140)

    def flash_execution(self, price: float, side: Optional[str] = None):
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
        if self.auto_center_enabled:
            self._scroll_to_center(animated=True)

    def _refresh_marks_only(self):
        # mark만 바꾼 후 렌더
        self.renderer.render(self.engine.rows)
        if self.auto_center_enabled:
            self._scroll_to_center(animated=False)

        # 살짝 pulse
        center_idx = self._find_center_index()
        if center_idx is not None:
            self.renderer.pulse_center(center_idx, ms=120)

    def _shift_rows(self, tick_move: int):
        """
        tick_move > 0 : 기준가 상승 → 화면은 "위로 올라가는 느낌"
        tick_move < 0 : 기준가 하락 → 화면은 "아래로 내려가는 느낌"
        """
        rows = self.engine.rows
        if not rows:
            return

        # tick_move만큼 한 칸씩 밀기
        if tick_move > 0:
            for _ in range(tick_move):
                # 위 한 줄 제거
                rows.pop(0)
                # 아래 새 row 추가 (마지막 가격에서 -tick)
                new_price = round(rows[-1].price - self.tick_size, 2)
                rows.append(self._make_empty_row(new_price))
        else:
            for _ in range(abs(tick_move)):
                rows.pop()  # 아래 제거
                new_price = round(rows[0].price + self.tick_size, 2)
                rows.insert(0, self._make_empty_row(new_price))

        # center/ls 마킹은 build에서 다시 세팅되지만, 시각적 일관성을 위해 1차 반영
        for i, r in enumerate(rows):
            r.is_center = (i == ORDERBOOK_DEPTH)
            r.is_ls_price = (r.price == round(self.center_price, 2))

        self.engine.apply_protections(self._protections)

    def _make_empty_row(self, price: float) -> OrderBookRow:
        # ✅ 네가 말한 make_empty_row "실제 구현"
        return OrderBookRow(price=round(float(price), 2))

    def _scroll_to_center(self, animated: bool = True):
        idx = self._find_center_index()
        if idx is None:
            return

        # 중앙에 유지하려면 실제 목표 스크롤 값을 계산해야 함
        item = self.table.item(idx, self.COL_PRICE)
        if not item:
            return

        sb = self.table.verticalScrollBar()
        cur = sb.value()

        # Qt가 목표값을 계산하도록 한번 요청
        self.table.scrollToItem(item, self.table.ScrollHint.PositionAtCenter)
        target = sb.value()
        sb.setValue(cur)

        if animated:
            self._animate_scroll(cur, target, duration=140)
        else:
            sb.setValue(target)

    def _animate_scroll_by_ticks(self, tick_move: int):
        """
        shift 후 방향감을 조금 더 주기 위해 살짝 스크롤 애니메이션.
        """
        sb = self.table.verticalScrollBar()
        cur = sb.value()

        # rowHeight가 0일 수 있어 안전 처리
        rh = self.table.rowHeight(0) or 18
        step = int(rh * abs(tick_move))

        # tick_move > 0(상승) → 위로 올라가는 느낌: 스크롤 값을 '감소'
        target = cur - step if tick_move > 0 else cur + step

        # 범위 클램프
        target = max(sb.minimum(), min(sb.maximum(), target))
        self._animate_scroll(cur, target, duration=120)

        # 애니메이션 후 다시 center로 정렬(살짝 안정감)
        QTimer.singleShot(140, lambda: self._scroll_to_center(animated=True))

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

    def on_orderbook_click(self, row, col):

        # -------------------------
        # 가격 가져오기 (공통)
        # -------------------------
        item = self.table.item(row, self.COL_PRICE)
        if not item:
            return

        try:
            price = float(item.text().replace(",", ""))
        except ValueError:
            return

        self.priceClicked.emit(price)

        qty = 1

        # =====================================================
        # ✅ 주문 허용 컬럼 (화이트리스트)
        # =====================================================
        # 지정가 SELL
        if col == self.renderer.COL_SELL:
            self.order_controller.place_limit_from_book(
                side="SELL",
                price=price,
                qty=qty,
            )
            return

        # 지정가 BUY
        if col == self.renderer.COL_BUY:
            self.order_controller.place_limit_from_book(
                side="BUY",
                price=price,
                qty=qty,
            )
            return

        # 시장가 SELL (MIT)
        if col == self.renderer.COL_MIT_SELL:
            self.order_controller.place_market_from_book(
                side="SELL",
                qty=qty,
            )
            return

        # 시장가 BUY (MIT)
        if col == self.renderer.COL_MIT_BUY:
            self.order_controller.place_market_from_book(
                side="BUY",
                qty=qty,
            )
            return

        # -------------------------
        # ❌ 나머지 모든 컬럼
        # -------------------------
        return

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








