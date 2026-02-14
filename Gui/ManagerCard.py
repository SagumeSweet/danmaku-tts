import logging
from collections.abc import Callable

from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout,
                               QComboBox, QLabel, QFrame)
from qasync import asyncSlot

from Clients import AITTSClient, TTSClient
from Clients.TTSClient import EdgeTTSClient
from Exceptions import ManagerCardException


class ManagerCard(QGroupBox):
    def __init__(self, title, client):
        super().__init__(title)
        self._tts_client = client

    @property
    def tts_client(self) -> TTSClient:
        return self._tts_client

    async def prepare_to_close(self):
        await self._tts_client.close()



class WeightsManagerCard(ManagerCard):
    def __init__(self, ai_tts_client: AITTSClient):
        super().__init__("模型权重管理", ai_tts_client)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # --- 当前状态展示区 ---
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 40);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 20);
            }
        """)
        status_layout = QVBoxLayout(self.status_frame)

        # 初始状态显示
        self.lbl_status_title = QLabel("当前状态: <b style='color: #FFA000;'>未载入</b>")
        self.lbl_status_detail = QLabel("版本: - | 角色: -")
        self.lbl_status_detail.setStyleSheet("color: #AAAAAA; font-size: 11px;")

        status_layout.addWidget(self.lbl_status_title)
        status_layout.addWidget(self.lbl_status_detail)
        layout.addWidget(self.status_frame)

        # --- 构版本选择 ---
        version_layout = QHBoxLayout()
        self.version_combo = QComboBox()
        self.version_combo.addItems(["v1", "v2", "v2Pro", "v2ProPlus", "v3", "v4"])
        # 默认同步 client 的初始版本
        self.version_combo.setCurrentText(self._tts_client.ai_config.version)
        self.version_combo.currentTextChanged.connect(self.on_version_changed)

        version_layout.addWidget(QLabel("架构版本:"))
        version_layout.addWidget(self.version_combo, 1)
        layout.addLayout(version_layout)

        # --- 3. 角色选择 ---
        self.name_combo = QComboBox()
        self.name_combo.setToolTip("选择已配对的 GPT 和 SoVITS 模型")
        self.name_combo.currentIndexChanged.connect(self.on_weights_changed)

        layout.addWidget(QLabel("当前角色:"))
        layout.addWidget(self.name_combo)
        # 初始化时自动执行一次扫描以填充下拉框（可选）
        self.on_version_changed()

    async def _change_status(self, work_func: Callable, status_name: str):
        # 锁定状态
        self.name_combo.setEnabled(False)
        self.version_combo.setEnabled(False)
        self.lbl_status_title.setText(f"当前状态: <b style='color: #FFA000;'>正在{status_name}...</b>")
        try:
            await work_func()
        except Exception as e:
            ex = ManagerCardException(f"{status_name}异常: {e}")
            logging.error(ex)
            self.lbl_status_title.setText(f"当前状态: <b style='color: #F44336;'>{status_name}异常</b>")
        finally:
            # 恢复状态
            self.name_combo.blockSignals(False)
            self.name_combo.setEnabled(True)
            self.version_combo.setEnabled(True)

    @asyncSlot()
    async def on_version_changed(self):
        """根据选定的版本，刷新角色列表"""
        version = self.version_combo.currentText()

        self.name_combo.clear()

        # 更新配置中的版本号
        self._tts_client.ai_config.version = version

        async def refresh():
            # 执行扫描
            await self._tts_client.scan_weights()
            names = self._tts_client.weights_names
            if names:
                self.name_combo.addItems(names)
                self.name_combo.setCurrentText(names[0])
                # 提示用户扫描成功，但尚未载入
                self.lbl_status_title.setText("当前状态: <b style='color: #03A9F4;'>已更新列表</b>")
            else:
                self.lbl_status_title.setText("当前状态: <b style='color: #F44336;'>未找到模型</b>")

        await self._change_status(refresh, "扫描")

    @asyncSlot()
    async def on_weights_changed(self, index):
        if index < 0:
            return
        weights_name = self.name_combo.currentText()
        version = self.version_combo.currentText()

        if not weights_name:
            return

        async def switch_weights():
            # --- 2. 执行切换逻辑 ---
            success = await self._tts_client.not_test.switch_weights(weights_name)
            if success:
                # --- 3. 更新成功后的状态文本 ---
                self.lbl_status_title.setText("当前状态: <b style='color: #4CAF50;'>已就绪</b>")
                self.lbl_status_detail.setText(f"版本: {version} | 角色: {weights_name}")
            else:
                self.lbl_status_title.setText("当前状态: <b style='color: #F44336;'>切换失败</b>")
                self.lbl_status_detail.setText(f"后端拒绝了角色: {weights_name} 的请求")

        await self._change_status(switch_weights, "切换模型")

class EdgeTTSManagerCard(ManagerCard):
    def __init__(self, edge_tts_client: EdgeTTSClient):
        super().__init__("Edge-TTS 管理", edge_tts_client)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Edge-TTS 配置面板 (待开发)"))


class OtherTTSManagerCard(ManagerCard):
    def __init__(self, client: TTSClient):
        super().__init__("其他 TTS", client)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("敬请期待..."))
