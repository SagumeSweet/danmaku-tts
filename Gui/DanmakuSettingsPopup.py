from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGraphicsDropShadowEffect


class DanmakuSettingsPopup(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(220, 220)
        self.setStyleSheet("""
            QFrame#SettingContainer { background-color: #252525; border: 1px solid #444; border-radius: 8px; }
            QLabel { color: #DDD; font-size: 13px; }
            QCheckBox { color: #DDD; font-size: 13px; spacing: 8px; }
            QSlider::handle:horizontal { background: #FFCA28; border-radius: 5px; width: 14px; height: 14px; }
        """)
        self.main_layout = QVBoxLayout(self)
        self.container = QFrame()
        self.container.setObjectName("SettingContainer")
        self.inner_layout = QVBoxLayout(self.container)
        self.title = QLabel("应用设置")
        self.title.setStyleSheet("font-weight: bold; color: white; padding: 5px; border-bottom: 1px solid #333;")
        self.inner_layout.addWidget(self.title)
        self.settings_layout = QVBoxLayout()
        self.inner_layout.addLayout(self.settings_layout)
        self.inner_layout.addStretch()
        self.main_layout.addWidget(self.container)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(Qt.GlobalColor.black)
        self.setGraphicsEffect(shadow)

    def add_setting_item(self, label_text, widget):
        item_layout = QVBoxLayout()
        if label_text: item_layout.addWidget(QLabel(label_text))
        item_layout.addWidget(widget)
        self.settings_layout.addLayout(item_layout)
        return widget