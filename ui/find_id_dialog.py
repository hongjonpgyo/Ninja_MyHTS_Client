from PyQt6.QtWidgets import QDialog
from PyQt6.uic import loadUi

class FindIdDialog(QDialog):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        loadUi("ui/find_id_dialog.ui", self)
        self.api = api

        self.btnFind.clicked.connect(self.find_id)
        self.btnCancel.clicked.connect(self.close)

    def find_id(self):
        email = self.editEmail.text().strip()
        if not email:
            self._error("이메일을 입력하세요.")
            return

        try:
            res = self.api.find_id(email)
            self._success(f"당신의 아이디는\n{res['email']} 입니다.")
        except Exception as e :
            print(e)
            self._error("일치하는 계정을 찾을 수 없습니다.")

    def _error(self, msg):
        self.labelResult.setStyleSheet("color:#e74c3c;")
        self.labelResult.setText(msg)

    def _success(self, msg):
        self.labelResult.setStyleSheet("color:#2ecc71;")
        self.labelResult.setText(msg)
