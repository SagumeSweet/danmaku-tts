import asyncio
import json
import logging
import os
import sys
import threading
from typing import override

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPlainTextEdit
from qasync import QEventLoop

from Enums import DefaultConfigName


class LogSignaler(QObject):
    signal = Signal(str)


class QtLogHandler(logging.Handler):
    def __init__(self, signaler):
        super().__init__()
        self.signaler = signaler

    @override
    def emit(self, record):
        msg = self.format(record)
        self.signaler.signal.emit(msg)

class SystemLogSignaler(QObject):
    signal = Signal(str)

class TTSHandlerTest:
    def __init__(self, client_class, gui_class=None):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.loop = QEventLoop(self.app)
        asyncio.set_event_loop(self.loop)

        self._config = None
        with open(r"..\configTemple.json", "r", encoding="utf-8") as f:
            self._config = json.load(f)[DefaultConfigName.tts_client]
        self.client = client_class(self._config)

        self.main_window = QMainWindow()
        self.main_window.setWindowTitle(f"TTS 集成测试 - {client_class.__name__}")
        self.main_window.resize(600, 500)

        central_widget = QWidget()
        self.layout = QVBoxLayout(central_widget)
        self.main_window.setCentralWidget(central_widget)

        if gui_class:
            self.gui_instance = gui_class(self.client)
            self.layout.addWidget(self.gui_instance)

        self.layout.addWidget(QLabel("系统日志输出:"))
        self.log_display = QPlainTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("background-color: #2b2b2b; color: #a9b7c6; font-family: Consolas;")
        self.layout.addWidget(self.log_display)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        self.log_signaler = LogSignaler()
        self.log_signaler.signal.connect(self.log_display.appendPlainText)

        handler = QtLogHandler(self.log_signaler)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s", "%H:%M:%S"))
        root_logger.addHandler(handler)

        # 创建系统信号器
        self.sys_log_signaler = SystemLogSignaler()
        self.sys_log_signaler.signal.connect(self.log_display.appendPlainText)

        # 启动劫持逻辑
        self._redirect_system_output()

    def _redirect_system_output(self):
        """劫持 C/C++ 层面的 stdout/stderr (如 FFmpeg 的输出)"""
        # 创建管道
        pipe_out, pipe_in = os.pipe()

        # 复制当前的 stderr (为了能恢复或者在必要时观察)
        # 并将 stderr (2) 重定向到管道的输入端
        os.dup2(pipe_in, sys.stderr.fileno())

        # 如果你想连 stdout (1) 也拦截，可以取消下面这行的注释
        # os.dup2(pipe_in, sys.stdout.fileno())

        def _read_pipe():
            # 这里必须在底层循环读取管道
            with os.fdopen(pipe_out, 'r', errors='replace') as pipe:
                for line in iter(pipe.readline, ''):
                    # 通过信号发送到 GUI
                    self.sys_log_signaler.signal.emit(line.strip())

        # 启动后台守护线程读取管道内容
        thread = threading.Thread(target=_read_pipe, daemon=True)
        thread.start()

    async def _input_loop(self):
        print(f"\n[{self.client.__class__.__name__}] 交互模式已启动")
        print(">>> 请在当前控制台输入文字并回车 (输入 'exit' 退出)")

        while True:
            text = await asyncio.to_thread(input, ">>> ")
            text = text.strip()

            if not text: continue
            if text.lower() == 'exit': break

            self.client.tts_queue.put_nowait(text)
            logging.info(f"已加入队列: {text}")

    async def _run_test_logic(self):
        try:
            self.client.start()
            self.main_window.show()
            await self._input_loop()
        except Exception as e:
            logging.error(f"异常: {e}")
        finally:
            logging.info("正在等待剩余语音播放完毕...")
            if hasattr(self.client, 'tts_queue'):
                await self.client.tts_queue.join()
            await self.client.close()
            self.app.quit()

    def run(self):
        with self.loop:
            self.loop.create_task(self._run_test_logic())
            self.loop.run_forever()