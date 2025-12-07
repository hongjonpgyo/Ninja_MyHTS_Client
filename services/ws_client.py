# services/ws_client.py
import asyncio
import json
import ssl
import websockets
from PyQt6.QtCore import QTimer


BINANCE_WS = "wss://stream.binance.com:9443/ws"


# ============================================================
# DEPTH WEBSOCKET CLIENT
# ============================================================
class DepthWSClient:
    def __init__(self, symbol: str, callback):
        self.symbol = symbol.lower()
        self.callback = callback
        self.is_running = False
        self.ws = None

    async def connect(self):
        """Binance Depth WS 연결 & 수신 루프"""
        stream = f"{self.symbol}@depth5@100ms"
        url = f"{BINANCE_WS}/{stream}"
        ssl_ctx = ssl._create_unverified_context()

        print(f"[DepthWS] Connect → {url}")
        self.is_running = True

        while self.is_running:
            try:
                async with websockets.connect(url, ssl=ssl_ctx) as ws:
                    self.ws = ws
                    print("[DepthWS] Connected")

                    async for msg in ws:
                        if not self.is_running:
                            break

                        data = json.loads(msg)

                        bids = [(float(p), float(q)) for p, q in data.get("bids", [])]
                        asks = [(float(p), float(q)) for p, q in data.get("asks", [])]

                        # UI 업데이트는 Qt Main Thread에서 실행
                        QTimer.singleShot(
                            0, lambda b=bids, a=asks: self.callback(b, a)
                        )

            except Exception as e:
                if not self.is_running:
                    break
                print(f"[DepthWS ERROR] {e}")
                await asyncio.sleep(0.5)

        print("[DepthWS] 종료됨")

    async def stop(self):
        """WS 완전 종료"""
        print("[DepthWS] STOP 요청")
        self.is_running = False

        try:
            if self.ws:
                await self.ws.close()
        except:
            pass

        self.ws = None

# ============================================================
# PRICE WEBSOCKET CLIENT
# ============================================================
# services/ws_client.py
import asyncio
import json
import websockets
from PyQt6.QtCore import QTimer


class PriceWSClient:
    def __init__(self, symbol: str, callback):
        self.symbol = symbol.lower()
        self.callback = callback
        self.running = False
        self.ws = None
        self.task = None

    async def start(self):
        """qasync 기반에서 안전하게 WS 시작"""
        await self.stop()          # 기존 소켓 정리
        self.running = True
        self.task = asyncio.create_task(self.run())

    async def run(self):
        """독립 실행 루프"""
        url = f"ws://127.0.0.1:9000/ws/price/{self.symbol}"
        print(f"[PriceWS] Connect → {url}")

        while self.running:
            try:
                async with websockets.connect(url) as ws:
                    self.ws = ws
                    print("[PriceWS] Connected")

                    while self.running:
                        try:
                            msg = await ws.recv()
                            data = json.loads(msg)
                            QTimer.singleShot(0, lambda d=data: self.callback(d))
                        except Exception as e:
                            print("[PriceWS recv error]", e)
                            break

            except asyncio.CancelledError:
                print("[PriceWS] cancelled")
                break

            except Exception as e:
                print("[PriceWS ERROR]", e)

            await asyncio.sleep(0.3)

        print("[PriceWS] 종료됨")

    async def stop(self):
        """WS 종료"""
        self.running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except:
                pass

        if self.ws:
            try:
                await self.ws.close()
            except:
                pass

        self.task = None
        self.ws = None


# services/ws_client.py
import websockets
import asyncio
import json

class ExecutionWSClient:
    def __init__(self, account_id, callback):
        self.account_id = account_id
        self.callback = callback
        self.running = True

    async def start(self):
        url = f"ws://127.0.0.1:9000/ws/executions/{self.account_id}"

        while self.running:
            try:
                async with websockets.connect(url) as ws:
                    print("[ExecWS] Connected")

                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        self.callback(data)

            except Exception as e:
                print("[ExecWS ERROR]", e)
                await asyncio.sleep(1)

    async def stop(self):
        self.running = False

class AccountWSClient:
    def __init__(self, account_id, on_update):
        self.url = f"ws://127.0.0.1:9000/ws/account/{account_id}"
        self.on_update = on_update
        self.running = True

    async def start(self):
        print(self.url)
        async with websockets.connect(self.url) as ws:
            while self.running:
                msg = await ws.recv()
                data = json.loads(msg)
                self.on_update(data)

    async def stop(self):
        self.running = False

