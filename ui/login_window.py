import asyncio
from PyQt6.QtWidgets import QDialog, QMessageBox, QLineEdit
from PyQt6.uic import loadUi

from services.api_client import APIClient
from ui.find_id_dialog import FindIdDialog
from ui.signup_dialog import SignupDialog
from ui.password_reset_confirm_dialog import PasswordResetConfirmDialog
from ui.utils.path_utils import resource_path


class LoginWindow(QDialog):
    def __init__(self, api_client: APIClient, on_login_success, parent=None):
        super().__init__(parent)
        loadUi(resource_path("ui/login_window.ui"), self)

        print("LoginWindow on_login_success:", on_login_success)
        print("type:", type(on_login_success))


        self.api = api_client              # ✅ 인스턴스 저장
        self.on_login_success = on_login_success

        self.btnLogin.clicked.connect(self._on_login_clicked)
        self.btnTogglePassword.clicked.connect(self.toggle_password)
        self.editPassword.returnPressed.connect(self.btnLogin.click)

        self.btnSignup.clicked.connect(self.open_signup)
        self.btnFindId.clicked.connect(self.open_find_id)
        self.btnResetPw.clicked.connect(self.open_reset_pw)

        self.editEmail.setText('demo@local')
        self.editPassword.setText('1234')

    def open_signup(self):
        print('signup')
        dlg = SignupDialog(self)
        if dlg.exec():
            self.labelStatus.setText("회원가입 완료! 로그인하세요.")

    def open_find_id(self):
        dlg = FindIdDialog(self.api, self)
        dlg.exec()

    def open_reset_pw(self):
        dlg = PasswordResetConfirmDialog(self.api, self)
        dlg.exec()

    def _on_login_clicked(self):
        asyncio.ensure_future(self._do_login())

    def toggle_password(self):
        if self.editPassword.echoMode() == QLineEdit.Password:
            self.editPassword.setEchoMode(QLineEdit.Normal)
        else:
            self.editPassword.setEchoMode(QLineEdit.Password)

    async def _do_login(self):
        email = self.editEmail.text().strip()
        password = self.editPassword.text().strip()
        try:
            login_res = await self.api.login(email, password)
            # print(login_res)
            if "access_token" in login_res:
                # QMessageBox.information(self, "Login", "로그인 성공!")

                # 🔥 이 값을 MainWindow로 전달해야 함
                token = login_res["access_token"]
                user = login_res["user_id"]
                account_id = login_res["account_id"]
                # print(token, user, account_id)
                # 🔥 MainWindow 열기
                if self.on_login_success:
                    self.on_login_success(token, user, account_id, email)
                self.accept()
                self.close()
            else:
                QMessageBox.warning(self, "Login Failed", str(login_res))

        except Exception as e:
            QMessageBox.warning(self, "Login Failed", str(e))
            print("LOGIN ERROR:", e)
