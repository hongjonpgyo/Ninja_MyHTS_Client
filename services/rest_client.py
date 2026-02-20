import aiohttp
from config.ls_settings import REST_URL

class RestClient:

    async def place_market(self, account_id, symbol, side, qty):
        url = f"{REST_URL}/orders/market"
        payload = {
            "account_id": account_id,
            "symbol_code": symbol,
            "side": side,
            "qty": qty,
        }

        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=payload) as r:
                return await r.json()

rest_client = RestClient()
