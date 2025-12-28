import asyncio
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.uic import loadUi

from services.api_client import APIClient


class PasswordResetRequestDialog(QDialog):
    """
    1️⃣ 비밀번호 재설정 요청 다이얼로그
    - 이메일 입력
    - reset token 발급 요청
    - 성공 시 PasswordResetConfirmDialog 호출
    """

    def __init__(self, api: APIClient, parent=None):
        super().__init__(parent)
        loadUi("ui/password_reset_request_dialog.ui", self)

        self.api = api

        self.btnRequest.clicked.connect(self.on_request_clicked)

    # -------------------------
    # Button Handler
    # -------------------------
    def on_request_clicked(self):
        asyncio.create_task(self._do_request())

    # -------------------------
    # Core Logic
    # -------------------------
    async def _do_request(self):
        email = self.editEmail.text().strip()

        if not email:
            QMessageBox.warning(self, "입력 오류", "이메일을 입력하세요.")
            return

        try:
            # 🔹 비밀번호 재설정 요청
            # 서버 API: POST /auth/password/reset/request
            res = await self.api.post(
                "/auth/password/reset/request",
                json={"email": email}
            )

            if not res.get("ok"):
                raise Exception(res.get("message", "요청 실패"))

            QMessageBox.information(
                self,
                "요청 완료",
                "비밀번호 재설정 토큰이 발급되었습니다.\n다음 단계로 진행하세요."
            )

            # 🔥 다음 단계: Confirm Dialog
            from ui.password_reset_confirm_dialog import PasswordResetConfirmDialog

            dlg = PasswordResetConfirmDialog(self.api, self)

            # 개발/테스트용: token 자동 입력
            token = res.get("token")
            if token:
                dlg.editToken.setText(token)

            dlg.exec()
            self.accept()

        except Exception as e:
            QMessageBox.warning(
                self,
                "오류",
                f"비밀번호 재설정 요청 실패\n\n{str(e)}"
            )
