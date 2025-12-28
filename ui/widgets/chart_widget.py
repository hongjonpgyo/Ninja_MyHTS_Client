# ui/widgets/chart_widget.py
from pathlib import Path
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

class ChartWidget(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)

        html_path = Path("ui/assets/chart.html").resolve()
        self.load(QUrl.fromLocalFile(str(html_path)))

        self.loadFinished.connect(self._on_loaded)

    def _on_loaded(self):
        # 🔥 여기서 차트 초기화
        self.page().runJavaScript("initChart();")

    def update_price(self, price: float):
        self.page().runJavaScript(f"updatePrice({float(price)})")
