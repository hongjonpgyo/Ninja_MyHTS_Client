import asyncio
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.uic import loadUi

from services.api_client import APIClient


class LoginWindow(QDialog):
    def __init__(self, api_client: APIClient, on_login_success, parent=None):
        super().__init__(parent)
        loadUi("ui/login_window.ui", self)

        self.api = api_client              # ✅ 인스턴스 저장
        self.on_login_success = on_login_success

        self.btnLogin.clicked.connect(self._on_login_clicked)

    def _on_login_clicked(self):
        asyncio.create_task(self._do_login())    # ✅ 코루틴 객체 전달

    async def _do_login(self):
        email = self.editEmail.text().strip()
        password = self.editPassword.text().strip()

        try:
            login_res = await self.api.login(email, password)

            if "access_token" in login_res:
                QMessageBox.information(self, "Login", "로그인 성공!")

                # 🔥 이 값을 MainWindow로 전달해야 함
                token = login_res["access_token"]
                user = login_res["user_id"]
                account_id = login_res["account_id"]

                # 🔥 MainWindow 열기
                if self.on_login_success:
                    self.on_login_success(token, user, account_id)
            else:
                QMessageBox.warning(self, "Login Failed", str(login_res))

        except Exception as e:
            QMessageBox.warning(self, "Login Failed", str(e))
            print("LOGIN ERROR:", e)
