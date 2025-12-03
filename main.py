import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from ui.main_window import MainWindow


def run():
    app = QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    w = MainWindow()
    w.show()   # 🔥 아주 중요

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    run()
