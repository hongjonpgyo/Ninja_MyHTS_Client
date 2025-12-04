import requests
from config.settings import REST_URL

class PositionApi:

    def get_my_positions(self, account_id: int):
        r = requests.get(f"{REST_URL}/positions/my?account_id={account_id}")
        return r.json()

    def close(self, position_id: int):
        r = requests.post(f"{REST_URL}/positions/close", json={"position_id": position_id})
        return r.json()
