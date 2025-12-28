from enum import Enum

class OrderClickMode(Enum):
    SINGLE = "single"
    DOUBLE = "double"


class UserTradeSetting:
    def __init__(self):
        # 주문 방식
        self.order_click_mode = OrderClickMode.DOUBLE

        # 추후 확장용
        self.confirm_toast = True
        self.enable_mit_click = True
