from typing import Dict, Tuple

class OrderController:
    """
    OrderController (Final)

    역할:
    - OrderBook 클릭으로 들어온 주문을
    - Backend API를 통해 DB에 INSERT
    - 체결/포지션/가격 판단 ❌ (오직 체결 이벤트만 신뢰)

    ❗ 원칙
    - 주문 = 생성
    - 체결 = 다른 파이프라인
    """

    def __init__(self, main_window, api):
        self.main = main_window
        self.api = api

        # ✅ 오더북 표시 전용 로컬 주문 저장소
        # key = (symbol, price, side)
        self._my_orders: Dict[Tuple[str, float, str], int] = {}

    # =====================================================
    # Public API (UI에서 호출)
    # =====================================================
    def place_limit_from_book(
        self,
        side: str,
        price: float,
        qty: int = 1,
    ):
        """
        OrderBook 클릭 전용 주문 생성
        """
        symbol = self.main.current_symbol
        account_id = self.main.account_id

        # 기본 방어
        if not symbol or not account_id:
            return

        if side not in ("BUY", "SELL"):
            return

        if price <= 0 or qty <= 0:
            return

        # 🔥 async 큐에 태움 (MainWindow 정책 준수)
        self.main.enqueue_async(
            self._create_order(
                symbol=symbol,
                side=side,
                price=price,
                qty=qty,
                account_id=account_id,
            )
        )

    def place_market_from_book(
            self,
            side: str,
            qty: int = 1,
    ):
        """
        OrderBook MIT 클릭 전용 시장가 주문
        """
        symbol = self.main.current_symbol
        account_id = self.main.account_id

        # 기본 방어
        if not symbol or not account_id:
            return

        if side not in ("BUY", "SELL"):
            return

        if qty <= 0:
            return

        self.main.enqueue_async(
            self._create_market_order(
                symbol=symbol,
                side=side,
                qty=qty,
                account_id=account_id,
            )
        )

    async def _create_order(
            self,
            symbol: str,
            side: str,
            price: float,
            qty: int,
            account_id: str,
    ):
        """
        실제 주문 INSERT 요청 (DB 기준, local 반영 ❌)
        """
        try:
            payload = {
                "account_id": str(account_id),
                "symbol": symbol,
                "side": side,
                "order_type": "LIMIT",
                "qty": qty,
                "request_price": price,
                "source": "ORDERBOOK",
            }

            # ✅ DB INSERT (LS 전송 ❌)
            await self.api.post("/ls/futures/orders", json=payload)

            # -------------------------
            # ✅ DB 기준으로 즉시 refresh
            # -------------------------
            # 주문 성공 직후 한 번 fetch
            self.main.enqueue_async(
                self.main.fetch_open_orders()
            )

            # -------------------------
            # Toast
            # -------------------------
            self.main.safe_ui(
                self.main.show_toast,
                f"[주문 성공] {symbol} {side} {qty} @ {price:,.2f}",
            )

        except Exception as e:
            print("[OrderController] create_order failed:", e)

            self.main.safe_ui(
                self.main.show_toast,
                "❌ 주문 실패",
            )

    async def _create_market_order(
            self,
            symbol: str,
            side: str,
            qty: int,
            account_id: str,
    ):
        """
        MARKET 주문 생성 (price는 백엔드에서 결정)
        """
        payload = {
            "account_id": str(account_id),
            "symbol": symbol,
            "side": side,
            "order_type": "MARKET",
            "qty": qty,
            "request_price": None,  # ✅ 명시
            "source": "ORDERBOOK_MIT",
        }

        await self.api.post("/ls/futures/orders", json=payload)

        # 주문 후 DB 기준 refresh
        self.main.enqueue_async(self.main.fetch_open_orders())

        self.main.safe_ui(
            self.main.show_toast,
            f"[시장가 주문] {symbol} {side} {qty}",
        )

    # =====================================================
    # Local my_orders 관리 (OrderBook 전용)
    # =====================================================
    def _increase_my_order(self, symbol: str, price: float, side: str):
        """
        주문 생성 시 오더북 표시용 건수 증가
        """
        key = (symbol, round(float(price), 2), side)
        self._my_orders[key] = self._my_orders.get(key, 0) + 1

        # 👉 OrderBookWidget는 View 이므로 그대로 전달
        self.main.safe_ui(
            self.main.orderbook.update_my_orders,
            dict(self._my_orders),
        )

    # =====================================================
    # 체결 / 취소 이벤트에서 호출될 인터페이스 (미래 확장)
    # =====================================================
    def remove_my_order(self, symbol: str, price: float, side: str):
        """
        ❗ 체결 or 취소 이벤트에서만 호출
        """
        key = (symbol, round(float(price), 2), side)
        if key not in self._my_orders:
            return

        self._my_orders[key] -= 1
        if self._my_orders[key] <= 0:
            del self._my_orders[key]

        self.main.safe_ui(
            self.main.orderbook.update_my_orders,
            dict(self._my_orders),
        )
