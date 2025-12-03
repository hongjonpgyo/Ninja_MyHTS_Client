import os

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.strip() + "\n")

# --------------------------------------------------------
# Main generator
# --------------------------------------------------------
def main():
    print("🚀 Generating HTS Client Project Structure...")

    BASE = os.path.abspath(os.path.dirname(__file__))

    # 1. Create folders
    folders = [
        "ui",
        "services",
        "widgets",
        "resources"
    ]

    for f in folders:
        mkdir(os.path.join(BASE, f))

    # --------------------------------------------------------
    # 2. main.py
    # --------------------------------------------------------
    write("main.py", """
import sys
import asyncio
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.uic import loadUi
from qasync import QEventLoop

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("ui/main_window.ui", self)

def run():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    run()
""")

    # --------------------------------------------------------
    # 3. requirements.txt
    # --------------------------------------------------------
    write("requirements.txt", """
PyQt6
requests
websockets
qasync
""")

    # --------------------------------------------------------
    # 4. README.md
    # --------------------------------------------------------
    write("README.md", """
# HTS_Client (PyQt)

## 설치 방법

""")

    # --------------------------------------------------------
    # 5. ui/main_window.ui (기본 UI)
    # --------------------------------------------------------
    write("ui/main_window.ui", """
<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="geometry">
   <rect><x>0</x><y>0</y><width>400</width><height>300</height></rect>
  </property>
  <property name="windowTitle">
   <string>HTS Client</string>
  </property>
  <widget class="QWidget" name="centralwidget">
   <layout class="QVBoxLayout">
    <item>
     <widget class="QLabel" name="labelPrice">
      <property name="text"><string>Price: -</string></property>
      <property name="alignment"><set>Qt::AlignCenter</set></property>
     </widget>
    </item>
    <item>
     <widget class="QPushButton" name="btnTest">
      <property name="text"><string>Test Button</string></property>
     </widget>
    </item>
   </layout>
  </widget>
 </widget>
 <resources/>
 <connections/>
</ui>
""")

    # --------------------------------------------------------
    # 6. services/api_client.py
    # --------------------------------------------------------
    mkdir("services")
    write("services/api_client.py", """
import requests

BASE_URL = "http://127.0.0.1:8000"

class APIClient:

    def get_price(self, symbol: str):
        url = f"{BASE_URL}/market/price/{symbol}"
        return requests.get(url).json()

    def place_market(self, account_id, symbol, side, qty):
        url = f"{BASE_URL}/orders/market"
        payload = {
            "account_id": account_id,
            "symbol": symbol,
            "side": side,
            "qty": qty
        }
        return requests.post(url, json=payload).json()
""")

    # --------------------------------------------------------
    # 7. services/ws_client.py
    # --------------------------------------------------------
    write("services/ws_client.py", """
import asyncio
import json
import websockets

class PriceWSClient:

    def __init__(self, symbol: str, callback):
        self.symbol = symbol.lower()
        self.callback = callback
        self.url = f"ws://127.0.0.1:8000/ws/price/{self.symbol}"

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.url) as ws:
                    async for msg in ws:
                        self.callback(json.loads(msg))
            except Exception as e:
                print("WS Error:", e)
                await asyncio.sleep(2)
""")

    # --------------------------------------------------------
    # 8. widgets/__init__.py
    # --------------------------------------------------------
    write("widgets/__init__.py", "")

    print("🎉 Client Project Structure Generated Successfully!")


# Run script
if __name__ == "__main__":
    main()
