import httpx
from services.api_client import APIClient


class LSAPIClient(APIClient):
    def __init__(self):
        super().__init__()

        # 🔥 핵심: httpx client를 LS base_url로 다시 생성
        self.base_url = "http://127.0.0.1:9001"
        self._client = httpx.AsyncClient(base_url=self.base_url)
