import asyncio
import json
import ssl
import websockets
from PyQt6.QtCore import QTimer


# -----------------------------------------------------------
# 공통 Base WebSocket Client
# -----------------------------------------------------------
class BaseWSClient:
    def __init__(self, url: str, callback):
        self.url = url
        self.callback = callback
        self.running = False
        self.task = None
        self.ws = None

        self.ssl_context = ssl._create_unverified_context()

    async def start(self):
        """기존 실행 중단 후 새로운 task 실행"""
        await self.stop()
        self.running = True
        self.task = asyncio.create_task(self.run())

    async def run(self):
        """재연결 루프"""
        print(f"[WS] Connecting → {self.url}")

        while self.running:
            try:
                if self.url.startswith("wss://"):
                    ws = await websockets.connect(self.url, ssl=self.ssl_context)
                else:
                    ws = await websockets.connect(self.url)

                self.ws = ws
                print(f"[WS] Connected → {self.url}")

                async for message in ws:
                    data = json.loads(message)
                    QTimer.singleShot(0, lambda d=data: self.callback(d))

            except Exception as e:
                print(f"[WS ERROR] {self.url} / {e}")
                await asyncio.sleep(1)

        print(f"[WS] Closed → {self.url}")

    async def stop(self):
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

        self.ws = None
        self.task = None

class DepthWSClient(BaseWSClient):
    def __init__(self, symbol, callback):
        self.symbol = symbol.lower()

        url = f"wss://stream.binance.com:9443/ws/{self.symbol}@depth20@100ms"

        super().__init__(url, callback)

    def _parse(self, data):
        bids = [(float(p), float(q)) for p, q in data.get("bids", [])]
        asks = [(float(p), float(q)) for p, q in data.get("asks", [])]
        return {"bids": bids, "asks": asks}


class PriceWSClient(BaseWSClient):
    def __init__(self, symbol, callback):
        self.symbol = symbol.lower()
        url = f"ws://127.0.0.1:9000/ws/price/{self.symbol}"
        super().__init__(url, callback)


class ExecutionWSClient(BaseWSClient):
    def __init__(self, account_id, callback):
        url = f"ws://127.0.0.1:9000/ws/executions/{account_id}"
        super().__init__(url, callback)


class AccountWSClient(BaseWSClient):
    def __init__(self, account_id, callback):
        url = f"ws://127.0.0.1:9000/ws/account/{account_id}"
        super().__init__(url, callback)


