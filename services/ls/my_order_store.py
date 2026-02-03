# services/my_order_store.py

class MyOrderStore:
    """
    내 주문 상태 저장소

    1️⃣ order_id 기반: 내 주문 판별
    2️⃣ symbol/side/price 기반: 오더북 잔량 표시
    """

    def __init__(self):
        # order_id -> order info
        self._orders: dict[str, dict] = {}

        # symbol -> side -> price -> cnt
        self._book: dict[str, dict] = {}

    # ==================================================
    # Order ID 기반 (핵심)
    # ==================================================
    def add_order(self, order: dict):
        """
        order 필수 필드:
        - order_id
        - symbol
        - side
        - price
        """
        oid = order.get("order_id")
        if not oid:
            return

        symbol = order["symbol"]
        side = order["side"]
        price = float(order["price"])

        self._orders[oid] = order
        self._increase_book(symbol, side, price)

    def remove_order(self, order_id: str):
        order = self._orders.pop(order_id, None)
        if not order:
            return

        self._decrease_book(
            order["symbol"],
            order["side"],
            float(order["price"]),
        )

    def has_order(self, order_id: str) -> bool:
        return order_id in self._orders

    def clear(self):
        self._orders.clear()
        self._book.clear()

    def get_my_orders(self):
        return self._orders

    # ==================================================
    # OrderBook 표시용
    # ==================================================
    def get_book(self, symbol: str) -> dict:
        """
        반환 구조:
        {
            "BUY": { price: cnt },
            "SELL": { price: cnt }
        }
        """
        return self._book.get(symbol, {"BUY": {}, "SELL": {}})

    # ==================================================
    # Internal helpers
    # ==================================================
    def _increase_book(self, symbol: str, side: str, price: float):
        book = self._book.setdefault(symbol, {})
        side_map = book.setdefault(side, {})
        side_map[price] = side_map.get(price, 0) + 1

    def _decrease_book(self, symbol: str, side: str, price: float):
        book = self._book.get(symbol)
        if not book:
            return

        side_map = book.get(side)
        if not side_map or price not in side_map:
            return

        side_map[price] -= 1
        if side_map[price] <= 0:
            del side_map[price]

        if not side_map:
            del book[side]

        if not book:
            del self._book[symbol]
