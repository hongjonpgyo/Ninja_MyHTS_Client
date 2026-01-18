# ui/controllers/background_controller.py
from PyQt6.QtCore import QTimer


class BackgroundController:
    def __init__(self, main_window, interval=0.5):
        self.main = main_window
        self.interval_ms = int(interval * 1000)

        self.timer = QTimer()
        self.timer.setInterval(self.interval_ms)
        self.timer.timeout.connect(self._on_tick)

    def start(self):
        if not self.timer.isActive():
            self.timer.start()

    async def stop(self):
        if self.timer.isActive():
            self.timer.stop()

    def _on_tick(self):
        # ✅ 비동기 작업 직접 실행 금지 -> 큐로만 전달
        if not getattr(self.main, "running", False):
            return

        if getattr(self.main, "account_id", None) is None:
            return

        self.main.enqueue_async(self.main.fetch_open_orders())
        self.main.enqueue_async(self.main.fetch_ls_quote())
        # self.main.enqueue_async(self.main.fetch_executions())
        self.main.enqueue_async(self.main.fetch_account_state())

        # self.main.enqueue_async(self.main.fetch_orderbook())
