# main.py
import os
import sys
import asyncio
from PyQt6.QtWidgets import QApplication, QStyleFactory
from qasync import QEventLoop

from api.ls.ls_api_client import LSAPIClient
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from PyQt6.QtGui import QFont, QPalette, QColor

from ui.utils.path_utils import resource_path

os.environ["QT_STYLE_OVERRIDE"] = "Fusion"

def load_qss(*paths):
    app = QApplication.instance()
    qss = ""
    for path in paths:
        full_path = resource_path(path)   # 🔥 여기 추가
        with open(full_path, "r", encoding="utf-8") as f:
            qss += f.read() + "\n"
    app.setStyleSheet(qss)
    app.setStyle("Fusion")
    # app.setFont(QFont("Pretendard", 10))
    app.setFont(QFont("Noto Sans KR", 10))

def force_dark_palette(app: QApplication):
    palette = QPalette()

    palette.setColor(QPalette.ColorRole.Window, QColor("#1f1f1f"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1f1f1f"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#2a2a2a"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2a2a2a"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#2a2a2a"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ff5555"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#3a7afe"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))

    app.setPalette(palette)

def main():
    app = QApplication(sys.argv)

    # 1️⃣ 스타일 고정
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setStyleSheet("""
    QTableWidget {
        border: none;
        background: #ffffff;
        gridline-color: #d8d8d8;
    }

    QHeaderView::section {
        border: 1px solid #d8d8d8;
        border-top: none;
        border-left: none;
        background: #f4f6f8;
    }
    """)

    force_dark_palette(app)
    # 2️⃣ 폰트
    app.setFont(QFont("Malgun Gothic", 10))

    # 3️⃣ QSS
    load_qss(
        # "ui/styles/common.qss",
        # "ui/styles/orderbook_base.qss",
        # "ui/styles/orderbook_dark.qss",
        # "ui/styles/light_hts.qss"
        "ui/styles/light_hts_classic.qss"
    )

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

    def on_login_success(token, user, account_id, email):
        nonlocal main_window, login_window

        main_window = MainWindow(api_client, show_login_window)
        main_window.init_user(token, user, account_id)
        main_window.setWindowTitle(f"HTS Client - {email}")
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
