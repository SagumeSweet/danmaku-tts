from PySide6.QtCore import Qt, QPoint, Signal, Slot, QTimer
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QFrame, QScrollArea, QPushButton,
                               QSlider, QStyle, QCheckBox)

from .DanmakuSettingsPopup import DanmakuSettingsPopup


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
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)


        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        self.update_background_style()
        self.container.setMouseTracking(True)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)

        # 顶栏
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(35)
        self.title_bar.setStyleSheet("background-color: rgba(255, 255, 255, 10); border-top-left-radius: 12px; border-top-right-radius: 12px;")
        t_layout = QHBoxLayout(self.title_bar)
        t_layout.setContentsMargins(10, 0, 5, 0)
        self.title_label = QLabel("弹幕面板")
        self.title_label.setStyleSheet("background: transparent; color: #AAA; font-weight: bold; border: none;")
        t_layout.addWidget(self.title_label)
        t_layout.addStretch()

        self.btn_lock = QPushButton("🔓")
        self.btn_lock.clicked.connect(self.toggle_lock)

        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.btn_settings.clicked.connect(self.toggle_settings_panel)

        self.btn_close = QPushButton()
        self.btn_close.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton))

        for b in [self.btn_lock, self.btn_settings, self.btn_close]:
            b.setStyleSheet("background: transparent; color: white; border: none; font-size: 15px; width: 30px;")
            t_layout.addWidget(b)

        self.container_layout.addWidget(self.title_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.danmu_layout = QVBoxLayout(self.scroll_content)
        self.danmu_layout.addStretch(1)  # 顶部弹簧
        self.danmu_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.danmu_layout.setSpacing(5)
        self.scroll.setWidget(self.scroll_content)
        self.container_layout.addWidget(self.scroll)
        self.main_layout.addWidget(self.container)
        self.resize(320, 480)
        self.setMouseTracking(True)

        self.settings_panel = DanmakuSettingsPopup()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)  # 允许调到 0
        self.opacity_slider.setValue(int(self._opacity * 100))
        self.settings_panel.add_setting_item("主窗口透明度", self.opacity_slider)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)

        self.scroll_check = QCheckBox("固定在最底层 (自动滚动)")
        self.scroll_check.setChecked(self._auto_scroll)
        self.settings_panel.add_setting_item("", self.scroll_check)
        self.scroll_check.stateChanged.connect(self.on_scroll_toggle)

    def init_window_configs(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)

    def toggle_lock(self):
        self._is_locked = not self._is_locked
        self.btn_lock.setText("🔒" if self._is_locked else "🔓")

    def toggle_settings_panel(self):
        if self.settings_panel.isVisible():
            self.settings_panel.hide()
        else:
            p = self.mapToGlobal(QPoint(self.width() + 5, 10))
            self.settings_panel.move(p)
            self.settings_panel.show()

    def update_background_style(self):
        alpha = int(self._opacity * 255)
        border = "1px solid rgba(255, 255, 255, 30)" if alpha > 20 else "none"
        self.container.setStyleSheet(f"#MainContainer {{ background-color: rgba(0, 0, 0, {alpha}); border-radius: 12px; border: {border}; }}")

    def on_opacity_changed(self, value):
        self._opacity = value / 100.0
        self.update_background_style()

    def on_scroll_toggle(self, state):
        self._auto_scroll = (state == Qt.CheckState.Checked.value)

    @Slot(str, str)
    def add_danmu(self, nick, content):
        text_html = f"<b style='color: #FFCA28; text-shadow: 1px 1px 2px black;'>{nick}:</b> <span style='color: white; text-shadow: 1px 1px 2px black;'>{content}</span>"
        lbl = QLabel(text_html)
        lbl.setStyleSheet("background: transparent; padding: 2px; font-size: 14px;")
        lbl.setWordWrap(True)
        self.danmu_layout.addWidget(lbl)
        while self.danmu_layout.count() > 51:
            item = self.danmu_layout.takeAt(1)
            if item.widget(): item.widget().deleteLater()
        if self._auto_scroll:
            bar = self.scroll.verticalScrollBar()
            QTimer.singleShot(50, lambda: bar.setValue(bar.maximum()))

    def get_resize_direction(self, pos):
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        m = self.edge_margin
        left, right = x < m, x > w - m
        top, bottom = y < m, y > h - m
        if left and top: return Qt.CursorShape.SizeFDiagCursor, "LT"
        if right and bottom: return Qt.CursorShape.SizeFDiagCursor, "RB"
        if left and bottom: return Qt.CursorShape.SizeBDiagCursor, "LB"
        if right and top: return Qt.CursorShape.SizeBDiagCursor, "RT"
        if left: return Qt.CursorShape.SizeHorCursor, "L"
        if right: return Qt.CursorShape.SizeHorCursor, "R"
        if top: return Qt.CursorShape.SizeVerCursor, "T"
        if bottom: return Qt.CursorShape.SizeVerCursor, "B"
        return Qt.CursorShape.ArrowCursor, None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self._is_locked:
            _, self.resize_dir = self.get_resize_direction(event.position().toPoint())
            if not self.resize_dir and event.position().y() < 40:
                self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        if not self._is_locked and not event.buttons():
            cursor_shape, _ = self.get_resize_direction(pos)
            self.setCursor(cursor_shape)
        if self.resize_dir and event.buttons() == Qt.MouseButton.LeftButton:
            rect = self.geometry()
            gp = event.globalPosition().toPoint()
            if "L" in self.resize_dir: rect.setLeft(gp.x())
            if "R" in self.resize_dir: rect.setRight(gp.x())
            if "T" in self.resize_dir: rect.setTop(gp.y())
            if "B" in self.resize_dir: rect.setBottom(gp.y())
            if rect.width() > 200 and rect.height() > 150: self.setGeometry(rect)
        elif not self._is_locked and event.buttons() == Qt.MouseButton.LeftButton and not self.resize_dir:
            if hasattr(self, 'drag_pos'): self.move(event.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        self.resize_dir = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
