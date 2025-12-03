import asyncio
import json
import websockets


class PriceWSClient:
    def __init__(self, symbol: str, callback):
        self.symbol = symbol.upper()
        self.callback = callback
        self.url = f"ws://127.0.0.1:9000/ws/price/{self.symbol.lower()}"
        self.running = True
        self.ws = None

    async def connect(self):
        """연결 & 재연결 루프"""
        while self.running:
            try:
                print(f"[WS] Connect → {self.url}")
                async with websockets.connect(self.url) as ws:
                    self.ws = ws
                    print("[WS] Connected!")

                    # 메시지 수신 루프
                    await self.receive_loop()

            except Exception as e:
                if not self.running:
                    break
                print(f"[WS ERROR] {e}")

            await asyncio.sleep(0.3)

        print("[WS] connect() 종료")

    async def receive_loop(self):
        """수신 루프"""
        while self.running:
            try:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                data = json.loads(msg)
                self.callback(data)

            except asyncio.TimeoutError:
                # timeout은 정상 → 다음 recv로 진행
                continue

            except websockets.ConnectionClosed:
                print("[WS] Connection Closed")
                break

            except Exception as e:
                print(f"[WS RECV ERROR] {e}")
                break

        print("[WS] receive_loop 종료")

    async def stop(self):
        """즉시 종료"""
        print("[WS] STOP 요청")
        self.running = False

        try:
            if self.ws:
                await self.ws.close()
        except:
            pass
        self.ws = None
