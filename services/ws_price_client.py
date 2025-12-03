import asyncio
import websockets
import json
from core.event_bus import event_bus
from services.data_cache import data_cache
from config.settings import WS_URL

class PriceWSClient:

    def __init__(self, symbol):
        self.symbol = symbol

    async def connect(self):
        url = f"{WS_URL}/price/{self.symbol.lower()}"
        print("[WS] Connect:", url)

        async with websockets.connect(url) as ws:
            async for msg in ws:
                data = json.loads(msg)
                data_cache.prices[self.symbol] = data
                event_bus.publish("price.update", {"symbol": self.symbol, "data": data})
