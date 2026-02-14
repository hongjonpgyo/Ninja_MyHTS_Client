import asyncio


class ReservationController:
    def __init__(self, widget, api, account_id, on_protection_changed=None):
        self.widget = widget
        self.api = api
        self.account_id = account_id
        self._rows: list[dict] = []
        # UI → Controller 이벤트 연결
        self.widget.on_cancel = self.cancel_reservation
        self.on_protection_changed = on_protection_changed

    # ----------------------------------
    async def refresh(self):
        try:
            rows = await self.api.get(
                "/ls/futures/reservation",
                params={"account_id": self.account_id},
            )
            # print("🔥 reservation rows:", rows, type(rows))
        except Exception as e:
            print("[ReservationController] refresh error:", e)
            rows = []

        self._rows = rows or []  # 🔥 캐시
        self.widget.update_rows(self._rows)

    # ----------------------------------
    async def cancel_reservation(self, reservation_id: int):
        try:
            # 1️⃣ 예약 취소
            await self.api.post(
                f"/ls/futures/reservation/{reservation_id}/cancel",
                json={}
            )

            # 2️⃣ 캐시에서 해당 reservation 찾기
            row = next(
                (r for r in self._rows if r.get("reservation_id") == reservation_id),
                None
            )
            symbol = row.get("symbol") if row else None

            if symbol:
                # 3️⃣ 보호주문 취소
                await self.api.post(
                    "/ls/futures/protections/cancel",
                    json={
                        "account_id": self.account_id,
                        "symbol": symbol,
                    }
                )

            # 🔥 4️⃣ 서버 기준으로 보호주문 다시 로딩
            if symbol and self.on_protection_changed:
                self.on_protection_changed(symbol)

            # 5️⃣ 예약 목록 재조회
            await self.refresh()

        except Exception as e:
            print("[RESERVATION CANCEL ERROR]", e)

    def on_status_event(self, event: dict):
        if event.get("source") != "RESERVATION":
            return

        reservation_id = event.get("reservation_id")
        status = event.get("status")

        if not reservation_id:
            return

        self.widget.update_status(reservation_id, status)
