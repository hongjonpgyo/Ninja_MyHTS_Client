# main.py
import sys
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication

from services.api_client import APIClient
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Qt + asyncio 통합
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    api_client = APIClient()
    login_window = None
    main_window = None

    def show_login_window():
        """로그아웃 등으로 다시 로그인창을 띄울 때 사용"""
        nonlocal login_window, main_window

        # 메인윈도우가 떠있으면 닫기
        if main_window:
            main_window.close()

        login_window = LoginWindow(api_client, on_login_success)
        login_window.show()

    def on_login_success(token, user, account_id):
        """LoginWindow에서 로그인 성공 시 호출하는 콜백"""
        nonlocal login_window, main_window

        main_window = MainWindow(api_client, show_login_window)
        main_window.init_user(token, user, account_id)
        main_window.show()

        if login_window:
            login_window.close()
            login_window = None

    # 최초 로그인 창 표시
    show_login_window()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
