class ReservationController:
    def __init__(self, widget, api, account_id):
        self.widget = widget
        self.api = api
        self.account_id = account_id

        # UI → Controller 이벤트 연결
        self.widget.on_cancel = self.cancel_reservation

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

        self.widget.update_rows(rows or [])

    # ----------------------------------
    async def cancel_reservation(self, reservation_id: int):
        try:
            await self.api.post(
                f"/ls/futures/reservation/{reservation_id}/cancel",
                json={}
            )

            # ✅ 가장 안전한 방식: 재조회
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
