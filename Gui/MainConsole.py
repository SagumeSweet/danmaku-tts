import asyncio
import logging
import random
import sys

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QApplication
from qasync import QEventLoop

from Clients import TTSClient, DanmakuClient
from .WeightManageCard import WeightsManagerCard
from .Overlay import OverlayPanel


class MainConsole(QMainWindow):
    def __init__(self, tts_client: TTSClient, danmaku_client: DanmakuClient):
        super().__init__()
        self._tts_client: TTSClient = tts_client
        self._danmaku_client: DanmakuClient = danmaku_client

        self.setWindowTitle("弹幕控制台")
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E1E; }
            QLabel { color: white; font-family: "Microsoft YaHei"; }
            QPushButton#ActionBtn { 
                background-color: #FFCA28; color: #1E1E1E; font-weight: bold; 
                border-radius: 6px; font-size: 15px; padding: 10px;
            }
            QPushButton#ActionBtn:hover { background-color: #FFD54F; }
            QPushButton#ActionBtn:pressed { background-color: #FFA000; }
        """)

        self.panel = None
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel("弹幕控制台")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFCA28;")
        layout.addWidget(title)

        status_lbl = QLabel("状态: 运行中")
        status_lbl.setStyleSheet("color: #888; margin-bottom: 20px;")
        layout.addWidget(status_lbl)

        # 弹幕面板开关
        self.toggle_btn = QPushButton("开启弹幕面板")
        self.toggle_btn.setObjectName("ActionBtn")
        self.toggle_btn.clicked.connect(self.recreate_panel)
        layout.addWidget(self.toggle_btn)

        self.weights_manager = WeightsManagerCard(self._tts_client)
        layout.addWidget(self.weights_manager)

        layout.addStretch()

    def handle_toggle_panel(self):
        if self.panel.isVisible():
            self.panel.hide()
            self.toggle_btn.setText("开启弹幕面板")
        else:
            self.panel.show()
            self.toggle_btn.setText("隐藏弹幕面板")

    def recreate_panel(self):
        """销毁旧面板并创建一个新的面板"""

        if self.panel is not None:
            logging.info("正在销毁旧面板...")
            # 关闭设置窗口（如果它开着的话）
            if hasattr(self.panel, 'settings_panel'):
                self.panel.settings_panel.close()

            self.panel.close()
            self.panel.deleteLater()  # 确保内存释放
            self.panel = None
            self.toggle_btn.setText("开启弹幕面板")

        else:
            logging.info("正在创建面板...")
            self.panel = OverlayPanel(self._tts_client, self._danmaku_client)

            # 必须重新连接信号，否则新面板接收不到数据
            self.panel.new_danmu_signal.connect(self.panel.add_danmu)
            self.panel.btn_close.clicked.connect(self.recreate_panel)

            self.panel.show()
            self.toggle_btn.setText("关闭当前面板")

    def closeEvent(self, event):
        """重写关闭事件，确保子窗口一起关闭"""
        if self.panel:
            self.panel.close()
        super().closeEvent(event)


# --- 运行逻辑 ---
async def simulate_danmu(console):
    """模拟外部弹幕涌入"""
    users = ["猫哥", "咸鱼", "大佬A", "System", "路人"]
    msgs = ["66666", "这也太强了吧", "测试弹幕占位符", "老板大气！", "欢迎来到直播间"]
    while True:
        await asyncio.sleep(random.uniform(0.5, 2.0))
        try:
            if console.panel.isVisible():
                console.panel.new_danmu_signal.emit(random.choice(users), random.choice(msgs))
        except AttributeError:
            pass


def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    console = MainConsole()
    console.show()

    # 将任务绑定到控制台持有的面板上
    loop.create_task(simulate_danmu(console))

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
