# api/auth_api.py
import requests


class AuthApi:
    BASE_URL = "http://127.0.0.1:9000"

    def signup(self, email: str, password: str):
        url = f"{self.BASE_URL}/auth/signup"
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
