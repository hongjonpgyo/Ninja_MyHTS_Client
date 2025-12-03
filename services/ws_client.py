# services/ws_client.py
import asyncio
import json
import ssl
import websockets
from PyQt6.QtCore import QTimer


BINANCE_WS = "wss://stream.binance.com:9443/ws"


# -----------------------------
# DEPTH WS CLIENT
# -----------------------------
class DepthWSClient:
    def __init__(self, symbol, callback):
        self.symbol = symbol.lower()
        self.callback = callback
        self.is_running = False
        self.ws = None
        self._task = None

    async def connect(self):
        self.is_running = True

        stream = f"{self.symbol}@depth5@100ms"
        url = f"{BINANCE_WS}/{stream}"

        ssl_ctx = ssl._create_unverified_context()
        print(f"[DepthWS] Connect → {url}")

        while self.is_running:
            try:
                async with websockets.connect(url, ssl=ssl_ctx) as ws:
                    self.ws = ws
                    print("[DepthWS] Connected")

                    async for msg in ws:
                        data = json.loads(msg)

                        bids = [(float(p), float(q)) for p, q in data.get("bids", [])]
                        asks = [(float(p), float(q)) for p, q in data.get("asks", [])]

                        # ★ UI는 Qt Thread에서만 업데이트
                        QTimer.singleShot(0, lambda b=bids, a=asks:
                                          self.callback(b, a))

            except Exception as e:
                print(f"[DepthWS ERROR] {e}")
                await asyncio.sleep(1)

        print("[DepthWS] 종료됨")

    def stop(self):
        self.is_running = False


# -----------------------------
# PRICE WS CLIENT
# -----------------------------
class PriceWSClient:
    def __init__(self, symbol: str, callback):
        self.symbol = symbol.lower()
        self.callback = callback

        self.running = False
        self.ws = None

    async def connect(self):
        self.running = True
        url = f"ws://127.0.0.1:9000/ws/price/{self.symbol}"

        print(f"[WS] Connect → {url}")

        while self.running:
            try:
                async with websockets.connect(url) as ws:
                    self.ws = ws
                    print("[WS] Connected!")

                    await self.receive_loop()

            except Exception as e:
                if not self.running:
                    break
                print("[WS ERROR]", e)

            await asyncio.sleep(0.5)

        print("[WS] 종료")

    async def receive_loop(self):
        while self.running:
            try:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                data = json.loads(msg)

                # UI 업데이트 Qt thread에서 실행
                QTimer.singleShot(0, lambda d=data: self.callback(d))

            except asyncio.TimeoutError:
                continue
            except websockets.ConnectionClosed:
                break
            except Exception as e:
                print("[WS RECV ERROR]", e)
                break

    def stop(self):
        self.running = False
        try:
            if self.ws:
                asyncio.create_task(self.ws.close())
        except:
            pass
