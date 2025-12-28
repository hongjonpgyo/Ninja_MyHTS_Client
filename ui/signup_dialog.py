# ui/dialogs/signup_dialog.py
from PyQt6.QtWidgets import QDialog
from PyQt6.uic import loadUi

from api.auth_api import AuthApi


class SignupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi("ui/signup_dialog.ui", self)

        self.api = AuthApi()

        self.btnCancel.clicked.connect(self.reject)
        self.btnSignup.clicked.connect(self.on_signup)

    def on_signup(self):
        email = self.editEmail.text().strip()
        pw = self.editPassword.text()
        pw2 = self.editPasswordConfirm.text()

        if not email:
            self._error("이메일을 입력하세요")
            return

        if len(pw) < 6:
            self._error("비밀번호는 6자 이상이어야 합니다")
            return

        if pw != pw2:
            self._error("비밀번호가 일치하지 않습니다")
            return

        if not self.chkAgree.isChecked():
            self._error("약관 동의가 필요합니다")
            return

        try:
            res = self.api.signup(email, pw)

            if res.get("ok"):
                self.accept()
            else:
                self._error(res.get("error", "회원가입 실패"))

        except Exception as e:
            self._error(str(e))

    def _error(self, msg: str):
        self.labelError.setText(msg)
