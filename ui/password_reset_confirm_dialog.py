from PyQt6.QtWidgets import QDialog
from PyQt6.uic import loadUi

class PasswordResetConfirmDialog(QDialog):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        loadUi("ui/password_reset_confirm_dialog.ui", self)

        self.api = api_client

    def on_reset(self):
        token = self.editToken.text().strip()
        pw1 = self.editPassword.text()
        pw2 = self.editPasswordConfirm.text()

        if not token or not pw1:
            self.labelStatus.setText("모든 항목을 입력하세요.")
            return

        if pw1 != pw2:
            self.labelStatus.setText("비밀번호가 일치하지 않습니다.")
            return

        try:
            self.api.reset_password(token, pw1)
            self.labelStatus.setStyleSheet("color:#2ecc71;")
            self.labelStatus.setText("비밀번호 변경 완료")
        except Exception as e:
            self.labelStatus.setStyleSheet("color:#e74c3c;")
            self.labelStatus.setText(str(e))

    # password_reset_request_dialog.py
    async def _do_request(self):
        res = await self.api.request_password_reset(email)

        if res.get("ok"):

            dlg = PasswordResetConfirmDialog(self.api, self)

            # 🔥 개발모드면 token 자동 채움
            if res.get("token"):
                dlg.editToken.setText(res["token"])

            dlg.exec()
            self.accept()

