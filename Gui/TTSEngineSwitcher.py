from typing import Optional

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabBar, QStackedWidget)
from qasync import asyncSlot
import logging

from Clients import AITTSClient
from Clients.TTSClient import EdgeTTSClient, TTSClient
from .Overlay import OverlayPanel
from .ManagerCard import ManagerCard


class TTSEngineSwitcher(QWidget):
    def __init__(self, config: dict, danmaku_panel: OverlayPanel):
        super().__init__()
        self._config = config  # 这里的 client 应该是总控
        self.current_engine_ui: Optional[ManagerCard] = None
        self._danmaku_panel = danmaku_panel
        self._danmaku_panel.tts_client_signal.connect(self._danmaku_panel.set_tts_client)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 引擎选择标签栏
        self.tab_bar = QTabBar()
        self.tab_bar.addTab("GPT-SoVITS")
        self.tab_bar.addTab("Edge-TTS (微软)")
        self.tab_bar.addTab("更多引擎...")
        self.tab_bar.setStyleSheet("""
            QTabBar::tab {
                background: rgba(255, 255, 255, 10);
                color: #AAAAAA;
                padding: 8px 20px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: rgba(255, 255, 255, 25);
                color: white;
                border-bottom: 2px solid #03A9F4;
            }
            QTabBar::tab:hover {
                background: rgba(255, 255, 255, 20);
            }
        """)

        self.tab_bar.currentChanged.connect(self.on_engine_switched)

        # 内容容器
        self.container = QStackedWidget()

        layout.addWidget(self.tab_bar)
        layout.addWidget(self.container)

        # 默认初始化
        self.on_engine_switched(0)

    @asyncSlot()
    async def on_engine_switched(self, index):
        """切换引擎：销毁旧 UI，根据引擎类型创建新 UI"""
        logging.info("[EngineSwitcher] 切换 TTS 引擎")
        # --- 彻底销毁旧实例 ---
        if self.current_engine_ui:
            # 如果旧实例有特定的关闭逻辑（如下载任务取消），可以在这里调用
            await self.current_engine_ui.prepare_to_close()
            self.container.removeWidget(self.current_engine_ui)
            self.current_engine_ui.deleteLater()
            self.current_engine_ui = None

        # --- 根据索引创建对应的组件 ---
        try:
            if index == 0:
                from .ManagerCard import WeightsManagerCard
                self.current_engine_ui = WeightsManagerCard(AITTSClient(self._config))

            elif index == 1:
                from .ManagerCard import EdgeTTSManagerCard
                self.current_engine_ui = EdgeTTSManagerCard(EdgeTTSClient(self._config))

            else:
                from .ManagerCard import OtherTTSManagerCard
                self.current_engine_ui = OtherTTSManagerCard(TTSClient(self._config))

            # --- 挂载到容器 ---
            self.container.addWidget(self.current_engine_ui)
            self.container.setCurrentWidget(self.current_engine_ui)
            self._danmaku_panel.tts_client_signal.emit(self.current_engine_ui.tts_client)

            logging.info(f"已切换至引擎索引: {index}")

        except Exception as e:
            logging.error(f"切换 TTS 引擎面板失败: {e}")
