import json
import requests
from PyQt6.QtCore import QThread, pyqtSignal


class PriceStreamWorker(QThread):
    price_received = pyqtSignal(dict)

    def __init__(self, base_url: str, token: str | None = None):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._running = True

    def set_token(self, token: str | None):
        self.token = token

    def stop(self):
        self._running = False

    def run(self):
        url = f"{self.base_url}/ls/futures/price/live/stream"
        print("[SSE] connect ->", url)

        headers = {"Accept": "text/event-stream"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            with requests.get(url, stream=True, headers=headers, timeout=(3, None)) as r:
                print("[SSE] status:", r.status_code)
                print("[SSE] resp content-type:", r.headers.get("content-type"))

                # ❌ 여기서 200 아니면 SSE 못 받는 게 정상
                if r.status_code != 200:
                    # 응답 바디 조금 찍어보면 원인 바로 나옴(401/422/404 등)
                    try:
                        text = r.text[:300]
                    except Exception:
                        text = "<no body>"
                    print("[SSE] non-200 body:", text)
                    return

                # SSE는 라인 단위로 온다
                for line in r.iter_lines(decode_unicode=True):
                    if not self._running:
                        break
                    if not line:
                        continue

                    # heartbeat ":" 무시
                    if line.startswith(":"):
                        continue

                    if not line.startswith("data:"):
                        continue

                    payload = line.replace("data:", "", 1).strip()
                    try:
                        event = json.loads(payload)
                    except Exception:
                        # JSON이 아닌 경우 한번 찍어보면 원인 금방 잡힘
                        print("[SSE] bad json:", payload[:200])
                        continue

                    # 🔍 디버그
                    print("[SSE EVENT]", event.get("event_type"), event.get("symbol"))
                    self.price_received.emit(event)

        except Exception as e:
            print("[SSE] connect/read error:", e)


