# api/auth_api.py
import requests
from config.ls_settings import LS_BASE_URL

class AuthApi:

    def signup(self, email: str, password: str):
        url = f"{LS_BASE_URL}/auth/signup"
        res = requests.post(
            url,
            json={
                "email": email,
                "password": password,
            },
            timeout=3,
        )
        res.raise_for_status()
        return res.json()
