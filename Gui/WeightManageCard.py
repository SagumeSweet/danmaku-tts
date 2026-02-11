from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout,
                               QComboBox, QLabel, QPushButton, QFrame)
from PySide6.QtCore import Signal, Slot, Qt
from qasync import asyncSlot
import logging

from Clients import AITTSClient


class WeightsManagerCard(QGroupBox):
    def __init__(self, ai_tts_client):
        super().__init__("模型权重管理")
        self._ai_tts_client: AITTSClient = ai_tts_client

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # --- 1. 当前状态展示区 ---
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

        # --- 2. 架构版本选择 ---
        version_layout = QHBoxLayout()
        self.version_combo = QComboBox()
        self.version_combo.addItems(["v1", "v2", "v3", "v4"])
        # 默认同步 client 的初始版本
        self.version_combo.setCurrentText(self._ai_tts_client.ai_config.version)

        self.btn_refresh = QPushButton("扫描目录")
        self.btn_refresh.clicked.connect(self.on_refresh_clicked)

        version_layout.addWidget(QLabel("架构版本:"))
        version_layout.addWidget(self.version_combo, 1)
        version_layout.addWidget(self.btn_refresh)
        layout.addLayout(version_layout)

        # --- 3. 角色选择 ---
        self.name_combo = QComboBox()
        self.name_combo.setToolTip("选择已配对的 GPT 和 SoVITS 模型")

        layout.addWidget(QLabel("当前角色:"))
        layout.addWidget(self.name_combo)

        # --- 4. 载入按钮 ---
        self.btn_apply = QPushButton("载入角色权重")
        self.btn_apply.setFixedHeight(35)  # 加高一点更显眼
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        layout.addWidget(self.btn_apply)

        # 初始化时自动执行一次扫描以填充下拉框（可选）
        # self.on_refresh_clicked()

    @asyncSlot()
    async def on_refresh_clicked(self):
        """根据选定的版本，刷新角色列表"""
        version = self.version_combo.currentText()

        self.btn_refresh.setEnabled(False)
        self.btn_refresh.setText("扫描中...")
        self.name_combo.clear()

        # 更新配置中的版本号
        self._ai_tts_client.ai_config.version = version

        try:
            # 执行扫描
            await self._ai_tts_client.scan_weights()
            names = self._ai_tts_client.weights_names

            if names:
                self.name_combo.addItems(names)
                # 提示用户扫描成功，但尚未载入
                self.lbl_status_title.setText("当前状态: <b style='color: #03A9F4;'>已更新列表</b>")
            else:
                self.lbl_status_title.setText("当前状态: <b style='color: #F44336;'>未找到模型</b>")

        except Exception as e:
            logging.error(f"扫描模型失败: {e}")
            self.lbl_status_title.setText("当前状态: <b style='color: #F44336;'>扫描异常</b>")
        finally:
            self.btn_refresh.setEnabled(True)
            self.btn_refresh.setText("扫描目录")

    @asyncSlot()
    async def on_apply_clicked(self):
        model_name = self.name_combo.currentText()
        version = self.version_combo.currentText()

        if not model_name:
            return

        # --- 1. 状态锁定 ---
        self.btn_apply.setEnabled(False)
        self.btn_apply.setText("正在载入权重...")
        self.lbl_status_title.setText("当前状态: <b style='color: #FFA000;'>正在切换...</b>")

        try:
            # --- 2. 执行切换逻辑 ---
            success = await self._ai_tts_client.switch_weights(model_name)

            if success:
                # --- 3. 更新成功后的状态文本 ---
                self.lbl_status_title.setText("当前状态: <b style='color: #4CAF50;'>已就绪</b>")
                self.lbl_status_detail.setText(f"版本: {version} | 角色: {model_name}")
                logging.info(f"权重切换完成: {model_name}")
            else:
                self.lbl_status_title.setText("当前状态: <b style='color: #F44336;'>切换失败</b>")
                self.lbl_status_detail.setText(f"后端拒绝了角色: {model_name} 的请求")

        except Exception as e:
            logging.error(f"权重切换异常: {e}")
            self.lbl_status_title.setText("当前状态: <b style='color: #F44336;'>请求异常</b>")
        finally:
            # --- 4. 状态恢复 ---
            self.btn_apply.setEnabled(True)
            self.btn_apply.setText("载入角色权重")