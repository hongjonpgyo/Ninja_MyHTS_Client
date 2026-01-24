from PyQt6.QtWidgets import QMessageBox

class OrderController:
    def __init__(self, main_window, order_panel, api):
        self.main = main_window
        self.panel = order_panel
        self.api = api

        self.panel.btnBuy.clicked.connect(
            lambda: self.place("BUY")
        )
        self.panel.btnSell.clicked.connect(
            lambda: self.place("SELL")
        )

    # UI 이벤트 → 큐에만 태운다
    def place(self, side: str):
        self.main.enqueue_async(self._order_worker(side))

    async def _order_worker(self, side: str):
        try:
            qty = self.panel.get_qty()
            order_type = self.panel.get_order_type()
            symbol = self.main.current_symbol

            if qty <= 0:
                self.main.safe_ui(
                    QMessageBox.warning,
                    self.main, "Order", "수량 오류"
                )
                return

            if order_type == "Market":
                await self.api.order_market(
                    account_id=self.main.account_id,
                    symbol=symbol,
                    side=side,
                    qty=qty,
                )
            else:
                price = self.panel.get_limit_price()
                if not price:
                    self.main.safe_ui(
                        QMessageBox.warning,
                        self.main, "Order", "가격 입력 필요"
                    )
                    return

                await self.api.order_limit(
                    account_id=self.main.account_id,
                    symbol=symbol,
                    side=side,
                    qty=qty,
                    price=price,
                )

            # ✅ UI는 반드시 safe_ui
            self.main.safe_ui(
                QMessageBox.information,
                self.main, "Order", f"{side} 주문 완료"
            )

        except Exception as e:
            print("[Order ERROR]", e)
            self.main.safe_ui(
                QMessageBox.warning,
                self.main, "Order Error", str(e)
            )

    # 🔥 오더북에서 들어오는 지정가 주문
    def place_limit_from_book(self, side: str, price: float, qty: float):
        self.main.enqueue_async(
            self._limit_from_book_worker(side, price, qty)
        )

    async def _limit_from_book_worker(self, side, price, qty):
        try:
            symbol = self.main.current_symbol

            if qty <= 0:
                return

            await self.api.order_limit(
                account_id=self.main.account_id,
                symbol=symbol,
                side=side,
                qty=qty,
                price=price,
            )

            self.main.safe_ui(
                lambda: print(f"[ORDERBOOK] {side} {price} x {qty} 주문 접수")
            )

        except Exception as e:
            print("[Orderbook Order ERROR]", e)




