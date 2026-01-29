import json
import requests
from PyQt6.QtCore import QThread, pyqtSignal


class PriceStreamWorker(QThread):
    price_received = pyqtSignal(dict)

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        url = f"{self.base_url}/ls/futures/price/stream"

        with requests.get(url, stream=True) as r:
            for line in r.iter_lines():
                if not self._running:
                    break

                if not line:
                    continue

                text = line.decode("utf-8")
                if not text.startswith("data:"):
                    continue

                try:
                    event = json.loads(text.replace("data:", "").strip())
                except Exception:
                    continue

                self.price_received.emit(event)
