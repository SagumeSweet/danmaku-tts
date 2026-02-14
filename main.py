import asyncio
import json
import logging
import sys

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from Gui import MainConsole


def main(conf_path: str = r".\configTemple.json"):
    # 初始化日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    with open(conf_path, "r", encoding="utf-8") as f:
        conf = json.load(f)
    # 初始化 Qt 应用
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 启动 GUI
    console = MainConsole(conf)
    console.show()
    # loop.create_task(rsocket_worker(rsocket_uri, console, queue))
    with loop:
        loop.run_forever()


if __name__ == '__main__':
    main()
