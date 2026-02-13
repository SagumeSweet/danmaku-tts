from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton

from Models import Config
from .Overlay import OverlayPanel
from .TTSEngineSwitcher import TTSEngineSwitcher


class MainConsole(QMainWindow):
    def __init__(self, config: dict, queue):
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

        self.panel = OverlayPanel()
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

        status_lbl = QLabel("状态: 运行中")
        status_lbl.setStyleSheet("color: #888; margin-bottom: 20px;")
        layout.addWidget(status_lbl)

        # 弹幕面板开关
        self.toggle_btn = QPushButton("开启弹幕面板")
        self.toggle_btn.setObjectName("ActionBtn")
        self.toggle_btn.clicked.connect(self.recreate_panel)
        layout.addWidget(self.toggle_btn)

        self.engine_switcher = TTSEngineSwitcher(self._config.tts_client, self.panel, queue)
        layout.addWidget(self.engine_switcher)

        layout.addStretch()

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
        super().closeEvent(event)
