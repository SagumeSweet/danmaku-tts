import sys
import asyncio
import random
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QFrame, QScrollArea, QPushButton,
                               QSlider, QStyle, QGraphicsDropShadowEffect,
                               QCheckBox, QMainWindow, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, QPoint, Signal, Slot, QTimer
from qasync import QEventLoop


class SettingsPopup(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setFixedSize(220, 220)
        self.setStyleSheet("""
            QFrame#SettingContainer { background-color: #252525; border: 1px solid #444; border-radius: 8px; }
            QLabel { color: #DDD; font-size: 13px; }
            QCheckBox { color: #DDD; font-size: 13px; spacing: 8px; }
            QSlider::handle:horizontal { background: #FFCA28; border-radius: 5px; width: 14px; height: 14px; }
        """)
        self.main_layout = QVBoxLayout(self)
        self.container = QFrame();
        self.container.setObjectName("SettingContainer")
        self.inner_layout = QVBoxLayout(self.container)
        self.title = QLabel("应用设置")
        self.title.setStyleSheet("font-weight: bold; color: white; padding: 5px; border-bottom: 1px solid #333;")
        self.inner_layout.addWidget(self.title)
        self.settings_layout = QVBoxLayout();
        self.inner_layout.addLayout(self.settings_layout)
        self.inner_layout.addStretch();
        self.main_layout.addWidget(self.container)
        shadow = QGraphicsDropShadowEffect(self);
        shadow.setBlurRadius(15);
        shadow.setColor(Qt.black)
        self.setGraphicsEffect(shadow)

    def add_setting_item(self, label_text, widget):
        item_layout = QVBoxLayout()
        if label_text: item_layout.addWidget(QLabel(label_text))
        item_layout.addWidget(widget);
        self.settings_layout.addLayout(item_layout)
        return widget


class OverlayPanel(QWidget):
    new_danmu_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        self._is_locked = False
        self._opacity = 0.8
        self._auto_scroll = True
        self.drag_pos = QPoint()
        self.edge_margin = 6
        self.resize_dir = None

        self.init_window_configs()
        self.init_ui()
        self.setMouseTracking(True)

        self.settings_panel = SettingsPopup()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)  # 允许调到 0
        self.opacity_slider.setValue(int(self._opacity * 100))
        self.settings_panel.add_setting_item("主窗口透明度", self.opacity_slider)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)

        self.scroll_check = QCheckBox("固定在最底层 (自动滚动)")
        self.scroll_check.setChecked(self._auto_scroll)
        self.settings_panel.add_setting_item("", self.scroll_check)
        self.scroll_check.stateChanged.connect(self.on_scroll_toggle)

    def init_window_configs(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self);
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.container = QFrame();
        self.container.setObjectName("MainContainer")
        self.update_background_style()
        self.container.setMouseTracking(True)
        self.container_layout = QVBoxLayout(self.container);
        self.container_layout.setContentsMargins(0, 0, 0, 0)

        # 顶栏
        self.title_bar = QFrame();
        self.title_bar.setFixedHeight(35)
        self.title_bar.setStyleSheet("background-color: rgba(255, 255, 255, 10); border-top-left-radius: 12px; border-top-right-radius: 12px;")
        t_layout = QHBoxLayout(self.title_bar);
        t_layout.setContentsMargins(10, 0, 5, 0)
        self.title_label = QLabel("弹幕面板")
        self.title_label.setStyleSheet("color: #AAA; font-weight: bold; border: none;")
        t_layout.addWidget(self.title_label);
        t_layout.addStretch()

        self.btn_lock = QPushButton("🔓");
        self.btn_lock.clicked.connect(self.toggle_lock)

        self.btn_settings = QPushButton();
        self.btn_settings.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.btn_settings.clicked.connect(self.toggle_settings_panel)

        self.btn_close = QPushButton();
        self.btn_close.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))

        for b in [self.btn_lock, self.btn_settings, self.btn_close]:
            b.setStyleSheet("background: transparent; color: white; border: none; font-size: 15px; width: 30px;")
            t_layout.addWidget(b)

        self.container_layout.addWidget(self.title_bar)

        self.scroll = QScrollArea();
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll_content = QWidget();
        self.scroll_content.setStyleSheet("background: transparent;")
        self.danmu_layout = QVBoxLayout(self.scroll_content)
        self.danmu_layout.addStretch(1)  # 顶部弹簧
        self.danmu_layout.setAlignment(Qt.AlignBottom);
        self.danmu_layout.setSpacing(5)
        self.scroll.setWidget(self.scroll_content)
        self.container_layout.addWidget(self.scroll)
        self.main_layout.addWidget(self.container)
        self.resize(320, 480)

    def toggle_lock(self):
        self._is_locked = not self._is_locked
        self.btn_lock.setText("🔒" if self._is_locked else "🔓")

    def toggle_settings_panel(self):
        if self.settings_panel.isVisible():
            self.settings_panel.hide()
        else:
            p = self.mapToGlobal(QPoint(self.width() + 5, 10))
            self.settings_panel.move(p);
            self.settings_panel.show()

    def update_background_style(self):
        alpha = int(self._opacity * 255)
        border = "1px solid rgba(255, 255, 255, 30)" if alpha > 20 else "none"
        self.container.setStyleSheet(f"#MainContainer {{ background-color: rgba(0, 0, 0, {alpha}); border-radius: 12px; border: {border}; }}")

    def on_opacity_changed(self, value):
        self._opacity = value / 100.0;
        self.update_background_style()

    def on_scroll_toggle(self, state):
        self._auto_scroll = (state == Qt.Checked.value)

    @Slot(str, str)
    def add_danmu(self, nick, content):
        text_html = f"<b style='color: #FFCA28; text-shadow: 1px 1px 2px black;'>{nick}:</b> <span style='color: white; text-shadow: 1px 1px 2px black;'>{content}</span>"
        lbl = QLabel(text_html);
        lbl.setStyleSheet("background: transparent; padding: 2px; font-size: 14px;");
        lbl.setWordWrap(True)
        self.danmu_layout.addWidget(lbl)
        while self.danmu_layout.count() > 51:
            item = self.danmu_layout.takeAt(1)
            if item.widget(): item.widget().deleteLater()
        if self._auto_scroll:
            bar = self.scroll.verticalScrollBar()
            QTimer.singleShot(50, lambda: bar.setValue(bar.maximum()))

    def get_resize_direction(self, pos):
        x, y = pos.x(), pos.y();
        w, h = self.width(), self.height();
        m = self.edge_margin
        left, right = x < m, x > w - m;
        top, bottom = y < m, y > h - m
        if left and top: return Qt.SizeFDiagCursor, "LT"
        if right and bottom: return Qt.SizeFDiagCursor, "RB"
        if left and bottom: return Qt.SizeBDiagCursor, "LB"
        if right and top: return Qt.SizeBDiagCursor, "RT"
        if left: return Qt.SizeHorCursor, "L"
        if right: return Qt.SizeHorCursor, "R"
        if top: return Qt.SizeVerCursor, "T"
        if bottom: return Qt.SizeVerCursor, "B"
        return Qt.ArrowCursor, None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self._is_locked:
            _, self.resize_dir = self.get_resize_direction(event.position().toPoint())
            if not self.resize_dir and event.position().y() < 40:
                self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        if not self._is_locked and not event.buttons():
            cursor_shape, _ = self.get_resize_direction(pos)
            self.setCursor(cursor_shape)
        if self.resize_dir and event.buttons() == Qt.LeftButton:
            rect = self.geometry();
            gp = event.globalPosition().toPoint()
            if "L" in self.resize_dir: rect.setLeft(gp.x())
            if "R" in self.resize_dir: rect.setRight(gp.x())
            if "T" in self.resize_dir: rect.setTop(gp.y())
            if "B" in self.resize_dir: rect.setBottom(gp.y())
            if rect.width() > 200 and rect.height() > 150: self.setGeometry(rect)
        elif not self._is_locked and event.buttons() == Qt.LeftButton and not self.resize_dir:
            if hasattr(self, 'drag_pos'): self.move(event.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        self.resize_dir = None;
        self.setCursor(Qt.ArrowCursor)


# --- 主控界面 ---
class MainConsole(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("弹幕控制台")
        self.setFixedSize(400, 250)
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

        self.init_ui()

    def init_ui(self):
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

        # 切换按钮
        self.toggle_btn = QPushButton("开启弹幕面板")
        self.toggle_btn.setObjectName("ActionBtn")
        self.toggle_btn.clicked.connect(self.recreate_panel)
        layout.addWidget(self.toggle_btn)

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
            print(">>> 正在销毁旧面板...")
            # 关闭设置窗口（如果它开着的话）
            if hasattr(self.panel, 'settings_panel'):
                self.panel.settings_panel.close()

            self.panel.close()
            self.panel.deleteLater()  # 确保内存释放
            self.panel = None
            self.toggle_btn.setText("开启弹幕面板")

        else:
            print(">>> 正在创建面板...")
            self.panel = OverlayPanel()

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
