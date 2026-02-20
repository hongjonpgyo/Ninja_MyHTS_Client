import requests
from config.ls_settings import LS_BASE_URL

class FavoriteApiClient:
    def __init__(self, token: str, base_ws_url: str = LS_BASE_URL):
        self.base_url = base_ws_url
        self.headers = {
            "Authorization": f"Bearer {token}"
        }

    def list(self):
        r = requests.get(
            f"{self.base_url}/ls/futures/favorites",
            headers=self.headers,
            timeout=3
        )
        r.raise_for_status()
        return r.json()

    def add(self, symbol_code: str):
        r = requests.post(
            f"{self.base_url}/ls/futures/favorites",
            json={"symbol_code": symbol_code},
            headers=self.headers,
            timeout=3
        )
        r.raise_for_status()
        return r.json()

    def remove(self, symbol_code: str):
        r = requests.delete(
            f"{self.base_url}/ls/futures/favorites/{symbol_code}",
            headers=self.headers,
            timeout=3
        )
        r.raise_for_status()
        return r.json()
