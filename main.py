# main.py
import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from api.ls.ls_api_client import LSAPIClient
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from PyQt6.QtGui import QFont

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Pretendard", 12))
    app.setStyleSheet('* { font-family:"Pretendard"; }')

    # 🔥 Qt + asyncio 통합 루프
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    api_client = LSAPIClient()
    main_window = None
    login_window = None

    def show_login_window():
        nonlocal login_window
        login_window = LoginWindow(api_client, on_login_success)
        login_window.show()

    def on_login_success(token, user, account_id):
        nonlocal main_window, login_window

        main_window = MainWindow(api_client, show_login_window)
        main_window.init_user(token, user, account_id)
        main_window.show()

        if login_window:
            login_window.close()
            login_window = None

    show_login_window()

    # 🔥 여기서 run_forever
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
