import os

ROOT = "."

# 폴더 구조 정의
folders = [
    f"{ROOT}",
    f"{ROOT}/config",
    f"{ROOT}/core",
    f"{ROOT}/services",
    f"{ROOT}/ui",
    f"{ROOT}/ui/widgets",
    f"{ROOT}/ui/resources",
    f"{ROOT}/utils",
]

# 파일 템플릿
files = {
    f"{ROOT}/main.py": """import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop
from ui.main_window import MainWindow

def run():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    w = MainWindow()
    w.show()

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    run()
""",

    f"{ROOT}/hts_app.py": """# HTS 전체 초기화 (EventBus, Services, etc.)

from core.event_bus import event_bus
from services.data_cache import data_cache

def init_hts_app():
    print("[HTS] Application initialized")
""",

    f"{ROOT}/config/settings.py": """# Client configuration

REST_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws"
DEFAULT_SYMBOL = "BTCUSDT"
""",

    f"{ROOT}/config/colors.py": """# UI Color theme

PRIMARY = "#1e90ff"
DANGER = "#e74c3c"
SUCCESS = "#2ecc71"
BG = "#1f1f1f"
TEXT = "#ffffff"
""",

    f"{ROOT}/core/event_bus.py": """class EventBus:
    def __init__(self):
        self._subs = {}

    def subscribe(self, name, callback):
        if name not in self._subs:
            self._subs[name] = []
        self._subs[name].append(callback)

    def publish(self, name, data=None):
        if name in self._subs:
            for cb in self._subs[name]:
                cb(data)

event_bus = EventBus()
""",

    f"{ROOT}/core/state.py": """class GlobalState:
    def __init__(self):
        self.current_symbol = "BTCUSDT"

state = GlobalState()
""",

    f"{ROOT}/core/logger.py": """def log(msg):
    print(f"[HTS] {msg}")
""",

    f"{ROOT}/services/rest_client.py": """import aiohttp
from config.settings import REST_URL

class RestClient:

    async def place_market(self, account_id, symbol, side, qty):
        url = f"{REST_URL}/orders/market"
        payload = {
            "account_id": account_id,
            "symbol_code": symbol,
            "side": side,
            "qty": qty,
        }

        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=payload) as r:
                return await r.json()

rest_client = RestClient()
""",

    f"{ROOT}/services/ws_price_client.py": """import asyncio
import websockets
import json
from core.event_bus import event_bus
from services.data_cache import data_cache
from config.settings import WS_URL

class PriceWSClient:

    def __init__(self, symbol):
        self.symbol = symbol

    async def connect(self):
        url = f"{WS_URL}/price/{self.symbol.lower()}"
        print("[WS] Connect:", url)

        async with websockets.connect(url) as ws:
            async for msg in ws:
                data = json.loads(msg)
                data_cache.prices[self.symbol] = data
                event_bus.publish("price.update", {"symbol": self.symbol, "data": data})
""",

    f"{ROOT}/services/ws_order_client.py": """# 주문 체결 WebSocket (추후 확장)
""",

    f"{ROOT}/services/data_cache.py": """class DataCache:
    def __init__(self):
        self.prices = {}
        self.positions = {}
        self.orders = {}

data_cache = DataCache()
""",

    f"{ROOT}/ui/main_window.py": """from PyQt6.QtWidgets import QMainWindow
from PyQt6.uic import loadUi
import asyncio
from core.event_bus import event_bus
from services.ws_price_client import PriceWSClient
from core.state import state

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("HTS_Client/ui/main_window.ui", self)

        event_bus.subscribe("price.update", self.update_price)

        asyncio.create_task(self.start_ws())

    async def start_ws(self):
        self.ws = PriceWSClient(state.current_symbol)
        await self.ws.connect()

    def update_price(self, evt):
        if evt["symbol"] != state.current_symbol:
            return

        data = evt["data"]
        self.labelPrice.setText(f"{data['last']}")
""",

    f"{ROOT}/ui/widgets/price_panel.py": """# 가격 표시 패널
""",

    f"{ROOT}/ui/widgets/order_panel.py": """# 주문 화면 패널
""",

    f"{ROOT}/ui/widgets/position_table.py": """# 포지션 테이블
""",

    f"{ROOT}/ui/widgets/log_panel.py": """# 로그 패널
""",

    f"{ROOT}/utils/formatter.py": """def format_num(n):
    return f"{n:,.2f}"
""",

    f"{ROOT}/utils/threads.py": """# Qt thread helper
""",

    f"{ROOT}/ui/main_window.ui": """<?xml version="1.0" encoding="UTF-8"?>
<!-- Qt Designer에서 수정할 기본 UI 템플릿 -->
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="windowTitle">
   <string>HTS Client</string>
  </property>
  <widget class="QWidget" name="centralwidget">
   <widget class="QLabel" name="labelPrice">
    <property name="text">
     <string>Loading...</string>
    </property>
   </widget>
  </widget>
 </widget>
</ui>
""",
}


# -------------------------
# 실제 폴더·파일 생성 수행
# -------------------------

def make_all():
    print("\n📁 Creating HTS_Client structure...\n")

    # 폴더 생성
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

    # 파일 생성
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    print("✅ HTS_Client 구조 생성 완료!")


if __name__ == "__main__":
    make_all()
