# services/ws_client.py
import asyncio
import json
import ssl
import websockets


class BaseWSClient:
    def __init__(self, url: str, callback, main_window=None):
        self.url = url
        self.callback = callback
        self.main_window = main_window

        self.running = False
        self.task = None
        self.ws = None

        self.ssl_context = ssl._create_unverified_context()

    async def start(self):
        await self.stop()
        self.running = True
        self.task = asyncio.create_task(self.run())

    async def run(self):
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

                    # ✅ Qt/UI thread로 안전 진입 (qasync 재진입 폭발 방지)
                    if self.main_window and hasattr(self.main_window, "safe_ui"):
                        self.main_window.safe_ui(self.callback, data)
                    else:
                        # main_window 없으면 그냥 콜백
                        self.callback(data)

            except asyncio.CancelledError:
                break
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
    def __init__(self, symbol, callback, main_window=None):
        self.symbol = symbol.lower()
        url = f"wss://stream.binance.com:9443/ws/{self.symbol}@depth20@100ms"
        super().__init__(url, callback, main_window=main_window)


class PriceWSClient(BaseWSClient):
    def __init__(self, symbol, callback, main_window=None):
        self.symbol = symbol.lower()
        url = f"ws://127.0.0.1:9000/ws/price/{self.symbol}"
        super().__init__(url, callback, main_window=main_window)


# class ExecutionWSClient(BaseWSClient):
#     def __init__(self, account_id, callback, main_window=None):
#         url = f"ws://127.0.0.1:9000/ws/executions/{account_id}"
#         super().__init__(url, callback, main_window=main_window)


# class AccountWSClient(BaseWSClient):
#     def __init__(self, account_id, callback, main_window=None):
#         url = f"ws://127.0.0.1:9000/ws/account/{account_id}"
#         super().__init__(url, callback, main_window=main_window)

# services/ws_client.py 에 추가
#
# class TradesWSClient(BaseWSClient):
#     def __init__(self, symbol, callback, main_window=None):
#         self.symbol = symbol.lower()
#         url = f"ws://127.0.0.1:9000/ws/trades/{self.symbol}"
#         super().__init__(url, callback, main_window=main_window)  # ✅ 너 현재 BaseWSClient 시그니처 유지 기준

