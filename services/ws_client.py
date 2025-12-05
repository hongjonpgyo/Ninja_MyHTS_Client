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
        self.is_running = True
        self.ws = None

    async def connect(self):
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
                        # 중간에 stop()으로 is_running=False 되면 ws.close() 호출 → 여기서 ConnectionClosed 발생
                        if not self.is_running:
                            break

                        data = json.loads(msg)

                        bids = [(float(p), float(q)) for p, q in data.get("bids", [])]
                        asks = [(float(p), float(q)) for p, q in data.get("asks", [])]

                        # UI 업데이트
                        try:
                            self.callback(bids, asks)
                        except Exception as e:
                            print("[DepthWS CALLBACK ERROR]", e)

            except websockets.ConnectionClosed:
                print("[DepthWS] Connection closed")
                if not self.is_running:
                    break
                await asyncio.sleep(1)

            except Exception as e:
                print(f"[DepthWS] ERROR: {e}")
                if not self.is_running:
                    break
                await asyncio.sleep(1)

        print("[DepthWS] connect() 종료")

    async def stop(self):
        """외부에서 호출해서 WS를 확실히 종료"""
        print("[DepthWS] STOP 요청")
        self.is_running = False
        try:
            if self.ws:
                await self.ws.close()
        except Exception:
            pass
        self.ws = None


# -----------------------------
# PRICE WS CLIENT
# -----------------------------
class PriceWSClient:
    def __init__(self, symbol: str, callback):
        self.symbol = symbol.upper()
        self.callback = callback
        self.url = f"ws://127.0.0.1:9000/ws/price/{self.symbol.lower()}"
        self.running = True
        self.ws = None

    async def connect(self):
        while self.running:
            try:
                print(f"[WS] Connect → {self.url}")
                async with websockets.connect(self.url) as ws:
                    self.ws = ws
                    print("[WS] Connected!")
                    await self.receive_loop()
            except Exception as e:
                if not self.running:
                    break
                print(f"[WS ERROR] {e}")
            await asyncio.sleep(0.3)
        print("[WS] connect() 종료")

    async def receive_loop(self):
        while self.running:
            try:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                data = json.loads(msg)

                try:
                    self.callback(data)
                except Exception as e:
                    print(f"[WS CALLBACK ERROR] {e}")

            except asyncio.TimeoutError:
                continue
            except websockets.ConnectionClosed:
                print("[WS] Connection Closed")
                break
            except Exception as e:
                print(f"[WS RECV ERROR] {e}")
                break
        print("[WS] receive_loop 종료")

    async def stop(self):
        print("[WS] STOP 요청")
        self.running = False
        try:
            if self.ws:
                await self.ws.close()
        except Exception:
            pass
        self.ws = None