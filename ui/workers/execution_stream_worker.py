import json
import requests
from PyQt6.QtCore import QThread, pyqtSignal


class ExecutionStreamWorker(QThread):
    """
    SSE 체결현황 수신 워커
    """
    execution_received = pyqtSignal(dict)

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        url = f"{self.base_url}/ls/futures/execution/stream"

        with requests.get(url, stream=True) as r:
            for line in r.iter_lines():
                if not self._running:
                    break

                if not line:
                    continue

                text = line.decode("utf-8")

                # SSE data 라인만 처리
                if not text.startswith("data:"):
                    continue

                payload = text.replace("data:", "").strip()

                try:
                    event = json.loads(payload)
                except Exception:
                    continue

                self.execution_received.emit(event)
