from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton

from Clients import DanmakuClient
from Models import Config
from .Overlay import OverlayPanel
from .TTSEngineSwitcher import TTSEngineSwitcher


class MainConsole(QMainWindow):
    def __init__(self, config: dict):
        super().__init__()
        self._config: Config = Config(config)

        self.setWindowTitle("弹幕控制台")
        self.setMinimumSize(400, 600)
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
        self._danmaku_client = DanmakuClient(self._config.danmaku_client)
        self.panel = OverlayPanel(self._danmaku_client)
        self.panel.new_danmu_signal.connect(self.panel.add_danmu)
        self.panel.btn_close.clicked.connect(self.recreate_panel)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel("弹幕控制台")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFCA28;")
        layout.addWidget(title)

        self._status_lbl = QLabel("状态: 连接中")
        self._status_lbl.setStyleSheet("color: #888; margin-bottom: 20px;")
        self._danmaku_client.status_changed.connect(self.update_status_text)
        layout.addWidget(self._status_lbl)

        # 弹幕面板开关
        self.toggle_btn = QPushButton("开启弹幕面板")
        self.toggle_btn.setObjectName("ActionBtn")
        self.toggle_btn.clicked.connect(self.recreate_panel)
        layout.addWidget(self.toggle_btn)

        self.engine_switcher = TTSEngineSwitcher(self._config.tts_client, self.panel)
        layout.addWidget(self.engine_switcher)

        layout.addStretch()

    def update_status_text(self, status_msg: str):
        self._status_lbl.setText(f"状态: {status_msg}")
        if "连接异常" in status_msg:
            self._status_lbl.setStyleSheet("color: #FF5252; font-weight: bold;")  # 红色
        elif "已连接" in status_msg:
            self._status_lbl.setStyleSheet("color: #4CAF50; font-weight: bold;")  # 绿色
        else:
            self._status_lbl.setStyleSheet("color: #888;")  # 默认灰色

    def recreate_panel(self):
        """销毁旧面板并创建一个新的面板"""

        if self.panel is None:
            self.toggle_btn.setText("隐藏弹幕面板")
        elif self.panel.isVisible():
            self.panel.on_hide()
            self.toggle_btn.setText("显示弹幕面板")
        else:
            self.panel.on_show()
            self.toggle_btn.setText("隐藏弹幕面板")

    def closeEvent(self, event):
        """重写关闭事件，确保子窗口一起关闭"""
        if self.panel:
            self.panel.close()
        if self.engine_switcher:
            self.engine_switcher.close()
        super().closeEvent(event)
