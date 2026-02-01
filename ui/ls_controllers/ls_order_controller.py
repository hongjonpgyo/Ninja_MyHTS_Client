from typing import Dict, Tuple

import requests
from PyQt6.QtWidgets import QMessageBox


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

    def __init__(self, main_window, api, account_api):
        self.main = main_window
        self.api = api
        self.account_api = account_api  # 🔥 추가

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

    def place_market_close(self, symbol: str, side: str, qty: int):
        account_id = self.main.account_id
        if not symbol or not account_id or qty <= 0:
            return

        self.main.enqueue_async(
            self._create_market_order(
                symbol=symbol,
                side=side,  # ✅ 인자 그대로 사용
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
            account_id: int,
    ):
        """
        실제 주문 INSERT 요청 (DB 기준, local 반영 ❌)
        """
        try:
            payload = {
                "account_id": int(account_id),
                "symbol": symbol,
                "side": side,
                "order_type": "LIMIT",
                "qty": qty,
                "request_price": price,
                "source": "ORDERBOOK",
            }

            # ✅ DB INSERT (LS 전송 ❌)
            await self.api.post("/ls/futures/orders", json=payload)

            self._increase_my_order(
                symbol=symbol,
                price=price,
                side=side,
            )

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
            account_id: int,
            source: str = "ORDERBOOK",
    ):
        payload = {
            "account_id": int(account_id),
            "symbol": symbol,
            "side": side,
            "order_type": "MARKET",
            "qty": qty,
            "request_price": None,
            "source": source,
        }

        try:
            await self.api.post("/ls/futures/orders", json=payload)

            self.main.enqueue_async(self.main.fetch_open_orders)

            self.main.safe_ui(
                self.main.show_toast,
                f"[시장가 주문] {symbol} {side} {qty}",
            )

        except Exception as e:
            print("[OrderController] MARKET order failed:", e)

            self.main.safe_ui(
                self.main.show_toast,
                "❌ 시장가 주문 실패",
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
            self._build_my_orders_for_orderbook(),
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

        # self.main.safe_ui(
        #     self.main.orderbook.update_my_orders,
        #     dict(self._my_orders),
        # )
        self.main.safe_ui(
            self.main.orderbook.update_my_orders,
            self._build_my_orders_for_orderbook(),
        )

    # ---------------------------------
    # 🔐 포지션 보호 주문 (TP / SL)
    # ---------------------------------
    def place_protection_order(self, payload: dict):
        """
        UI → Controller → Async Worker
        """
        self.main.enqueue_async(
            self._protection_worker(payload)
        )

    async def _protection_worker(self, payload: dict):
        try:
            print("###############")
            print(payload)
            print("###############")
            # 🔑 account_id는 여기서 주입
            payload["account_id"] = self.main.account_id
            payload.setdefault("source", "UI")

            await self.api.place_protection_order(payload)

            self.main.safe_ui(
                QMessageBox.information,
                self.main, "Protection", "보호 주문 적용 완료"
            )

            # ✅ 핵심: 다시 조회
            rows = await self.api.get_protections(
                account_id=payload["account_id"],
                symbol=payload["symbol"],
            )

            self.main.safe_ui(
                self.main.protection_panel.load_protections,
                rows,
            )

        except Exception as e:
            print("[Protection ERROR]", e)

    def load_protections(self, symbol: str):
        self.main.enqueue_async(
            self._load_protections_worker(symbol)
        )

    async def _load_protections_worker(self, symbol: str):
        try:
            rows = await self.api.get_protections(
                account_id=self.main.account_id,
                symbol=symbol,
            )
            # ✅ 보호주문 패널에 반영
            self.main.safe_ui(
                self._apply_protections_to_ui,
                rows,
            )

        except Exception as e:
            print("[Load Protection ERROR]", e)

    def _apply_protections_to_ui(self, rows: list[dict]):
        print("[PROTECTIONS rows sample]", rows[:2])
        # 1️⃣ 보호 패널
        self.main.protection_panel.load_protections(rows)

        # 2️⃣ 🔥 오더북 (이게 핵심)
        if self.main.orderbook:
            self.main.orderbook.set_protections(rows)

    def _build_my_orders_for_orderbook(self) -> dict:
        """
        내부 my_orders → OrderBookEngine용 구조로 변환
        """
        out = {
            "BUY": {},
            "SELL": {},
        }

        for (symbol, price, side), cnt in self._my_orders.items():
            if symbol != self.main.current_symbol:
                continue

            p = round(float(price), 2)
            out[side][p] = out[side].get(p, 0) + cnt

        return out

    def cancel_protections(self, account_id: int, symbol: str):
        self.main.enqueue_async(
            self._cancel_protections_worker(account_id, symbol)
        )

    async def _cancel_protections_worker(self, account_id: int, symbol: str):
        try:
            await self.api.post(
                "/ls/futures/protections/cancel",
                json={
                    "account_id": account_id,
                    "symbol": symbol,
                }
            )

            # UI 반영
            self.main.safe_ui(
                self.main.protection_panel.clear
            )
            self.main.safe_ui(
                self.main.orderbook.set_protections,
                []
            )

        except Exception as e:
            print("[Cancel Protection ERROR]", e)

