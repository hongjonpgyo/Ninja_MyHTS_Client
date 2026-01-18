# services/account_ws_client.py
import asyncio
import json
import ssl
import websockets
from config.settings import LS_BASE_URL

class LSAccountWSClient:
    def __init__(
        self,
        token: str,
        account_id: int,
        callback,
        main_window,
        base_ws_url: str = LS_BASE_URL,
    ):
        """
        callback: callable(dict) -> None   (UI에서 실행될 함수)
        main_window: MainWindow (safe_ui 사용)
        """
        self.base_ws_url = base_ws_url.rstrip("/")
        self.token = token
        self.account_id = account_id
        self.callback = callback
        self.main_window = main_window

        self._running = False
        self._task: asyncio.Task | None = None

    # -------------------------------------------------
    async def start(self):
        if self._task and not self._task.done():
            return
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except Exception:
                pass
            self._task = None

    # -------------------------------------------------
    async def _run(self):
        url = (
            f"{self.base_ws_url}/ws/account"
            f"?token={self.token}&account_id={self.account_id}"
        )
        ssl_ctx = None
        if url.startswith("wss://"):
            ssl_ctx = ssl._create_unverified_context()

        while self._running:
            ws = None
            keep_task = None
            try:
                ws = await websockets.connect(url, ssl=ssl_ctx)

                # -----------------------------
                # keep-alive ping
                # -----------------------------
                async def keep_alive():
                    while self._running:
                        await asyncio.sleep(20)
                        try:
                            await ws.send("ping")
                        except Exception:
                            break

                keep_task = asyncio.create_task(keep_alive())

                # -----------------------------
                # message loop
                # -----------------------------
                while self._running:
                    msg = await ws.recv()
                    try:
                        data = json.loads(msg)
                    except Exception:
                        continue

                    # ✅ UI 스레드 안전 보장
                    try:
                        self.main_window.safe_ui(self.callback, data)
                    except Exception:
                        pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                if not self._running:
                    break
                print("[AccountWS] reconnecting...", e)
                await asyncio.sleep(1.0)
            finally:
                if keep_task:
                    keep_task.cancel()
                if ws:
                    try:
                        await ws.close()
                    except Exception:
                        pass
