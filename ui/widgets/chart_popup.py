# ui/popups/chart_popup.py
import os, json
from PyQt6.QtWidgets import QDialog, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl


class ChartPopup(QDialog):
    def __init__(self, symbol="BTCUSDT", parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"{symbol} Chart")
        self.resize(900, 600)

        self._is_loaded = False
        self._pending_candles = None   # 🔥 핵심

        layout = QVBoxLayout(self)
        self.web = QWebEngineView()
        layout.addWidget(self.web)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        chart_path = os.path.abspath(
            os.path.join(base_dir, "..", "assets", "chart", "chart.html")
        )

        self.web.loadFinished.connect(self._on_loaded)
        self.web.setUrl(QUrl.fromLocalFile(chart_path))

    # -----------------------------------
    def _on_loaded(self, ok: bool):
        print("[ChartPopup] chart.html loaded:", ok)
        if not ok:
            return

        self._is_loaded = True

        # 🔥 load 전에 들어온 데이터 처리
        if self._pending_candles is not None:
            self._send_candles(self._pending_candles)
            self._pending_candles = None

    # -----------------------------------
    def set_candles(self, candles: list[dict]):
        """
        외부에서 호출되는 API
        """
        if not self._is_loaded:
            # 아직 JS 준비 안 됨 → 저장
            self._pending_candles = candles
            return

        self._send_candles(candles)

    # -----------------------------------
    def _send_candles(self, candles):
        js = f"""
        if (window.setCandles) {{
            window.setCandles({json.dumps(candles)});
        }} else {{
            console.error("setCandles not ready (JS)");
        }}
        """
        self.web.page().runJavaScript(js)
