# main.py
import sys
import qasync
from PyQt6.QtWidgets import QApplication
import asyncio

from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    # 🔥 asyncio 이벤트 루프와 PyQt 이벤트루프 통합
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    w = MainWindow()
    w.show()

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
