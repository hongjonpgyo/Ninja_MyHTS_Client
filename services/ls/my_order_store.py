# services/my_order_store.py

class MyOrderStore:
    """
    내 주문 상태 저장소
    구조:
    {
        symbol: {
            "BUY": { price: cnt },
            "SELL": { price: cnt }
        }
    }
    """
    def __init__(self):
        self._data = {}

    def increase(self, symbol: str, price: float, side: str):
        book = self._data.setdefault(symbol, {})
        side_map = book.setdefault(side, {})
        side_map[price] = side_map.get(price, 0) + 1

    def decrease(self, symbol: str, price: float, side: str):
        book = self._data.get(symbol, {})
        side_map = book.get(side, {})
        if price not in side_map:
            return

        side_map[price] -= 1
        if side_map[price] <= 0:
            del side_map[price]

    def get(self, symbol: str):
        return self._data.get(symbol, {})

    def clear_symbol(self, symbol: str):
        self._data.pop(symbol, None)
