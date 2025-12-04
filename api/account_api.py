import requests
from config.settings import REST_URL

class AccountApi:

    def get_balance(self, account_id: int):
        r = requests.get(f"{REST_URL}/accounts/{account_id}/balance")
        return r.json()
