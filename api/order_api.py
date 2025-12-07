import requests
from config.settings import REST_URL


class OrderApi:

    def __init__(self):
        self.base = REST_URL

    # -------------------------------
    # 공통 GET
    # -------------------------------
    def _get(self, path, params=None):
        try:
            r = requests.get(self.base + path, params=params)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # -------------------------------
    # 공통 POST  ← ★ 새로 추가됨
    # -------------------------------
    def _post(self, path, json=None):
        try:
            r = requests.post(self.base + path, json=json)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ======================================================
    # API 함수들
    # ======================================================

    # 미체결 주문 조회
    def get_open_orders(self, account_id: int):
        return self._get(f"/orders/open/{account_id}")

    # 주문 취소 (복수)
    def cancel_orders(self, order_ids: list[int]):
        payload = {"order_ids": order_ids}
        return self._post("/orders/cancel_orders", json=payload)
