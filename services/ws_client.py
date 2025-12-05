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
class PriceWSClient:
    def __init__(self, symbol: str, callback):
        self.symbol = symbol.lower()
        self.callback = callback
        self.running = False
        self.ws = None

    async def connect(self):
        """백엔드 Price WS 연결 루프"""
        url = f"ws://127.0.0.1:9000/ws/price/{self.symbol}"
        print(f"[PriceWS] Connect → {url}")

        self.running = True

        while self.running:
            try:
                async with websockets.connect(url) as ws:
                    self.ws = ws
                    print("[PriceWS] Connected")

                    await self.receive_loop()

            except Exception as e:
                if not self.running:
                    break
                print("[PriceWS ERROR]", e)

            await asyncio.sleep(0.5)

        print("[PriceWS] 종료됨")

    async def receive_loop(self):
        while self.running:
            try:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                data = json.loads(msg)

                QTimer.singleShot(0, lambda d=data: self.callback(d))

            except asyncio.TimeoutError:
                continue
            except websockets.ConnectionClosed:
                break
            except Exception as e:
                print("[PriceWS RECV ERROR]", e)
                break

    async def stop(self):
        """WS 완전 종료"""
        print("[PriceWS] STOP 요청")
        self.running = False

        try:
            if self.ws:
                await self.ws.close()
        except:
            pass

        self.ws = None
