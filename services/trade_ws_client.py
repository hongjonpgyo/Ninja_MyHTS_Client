# services/ws/trade_ws_client.py
import asyncio
import json
import inspect
import websockets
from typing import Callable, Optional


class TradesWSClient:
    """
    Time & Sales 전용 WebSocket Client
    - symbol 단위 WS
    - 고빈도 데이터 대응
    - sync / async callback 모두 지원
    """

    def __init__(
        self,
        symbol: str,
        callback: Callable,
        base_url: str = "ws://127.0.0.1:9000",
    ):
        self.symbol = symbol.lower()
        self.url = f"{base_url}/ws/trades/{self.symbol}"
        self.callback = callback

        self._task: Optional[asyncio.Task] = None
        self._ws = None
        self._running = False

    # -----------------------------
    # Public API
    # -----------------------------
    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        self._running = False

        try:
            if self._ws:
                await self._ws.close()
        except Exception:
            pass

        if self._task:
            self._task.cancel()
            self._task = None

    # -----------------------------
    # Internal
    # -----------------------------
    async def _dispatch(self, data):
        """
        callback이 sync/async 인지 자동 판별
        """
        try:
            if inspect.iscoroutinefunction(self.callback):
                await self.callback(data)
            else:
                self.callback(data)
        except Exception as e:
            print("[TradesWSClient] callback error:", e)

    async def _run(self):
        """
        WS 수신 루프 (재연결 포함)
        """
        while self._running:
            try:
                print(f"[TradesWSClient] connect → {self.url}")

                async with websockets.connect(
                    self.url,
                    ping_interval=20,
                    ping_timeout=20,
                    max_queue=1000,   # 고빈도 보호
                ) as ws:
                    self._ws = ws
                    print("[TradesWSClient] connected")

                    async for msg in ws:
                        if not self._running:
                            break

                        try:
                            data = json.loads(msg)
                        except Exception:
                            data = msg

                        await self._dispatch(data)

            except asyncio.CancelledError:
                break

            except Exception as e:
                print("[TradesWSClient] ws error:", e)
                await asyncio.sleep(1.0)  # 재연결 딜레이

        print("[TradesWSClient] stopped")
