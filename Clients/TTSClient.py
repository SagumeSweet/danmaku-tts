import asyncio
import logging
import re
from collections import defaultdict
from contextlib import suppress
from typing import override

import aiohttp
from PySide6.QtCore import QUrl, QBuffer, QObject, QIODeviceBase, QByteArray
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from yarl import URL

from Exceptions import AIClientException
from Models import TTSClientConfig, AIClientConfig, AIWeightsPaths


class TTSClient(QObject):
    def __init__(self, config: dict, is_test: bool = True):
        super().__init__()
        self.config: TTSClientConfig = TTSClientConfig(config)
        self.tts_queue = asyncio.Queue()
        self._session = None
        self._running = False
        self._worker_task = None
        self._is_test: bool = is_test
        self.worker_close_task = None
        self._client_close_task = None

        # 初始化 Qt 播放器
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        self._q_data = None
        self._q_buffer = None

    @property
    def not_test(self) -> 'TTSClient':
        self._is_test = False
        return self

    async def _post_tts(self, target_url: URL, post_data: dict):
        async with self._session.post(target_url, json=post_data) as resp:
            if resp.status == 200:
                logging.debug("[TTS]成功接收生成语音")
                audio_data = await resp.read()
                await self._play_audio(audio_data)
            else:
                err_text = await resp.text()
                logging.error(f"[TTS]服务返回错误 [{resp.status}]: {err_text}")
                # 如果后端报错，等 1 秒再继续，避免日志刷屏
                await asyncio.sleep(1)

    def start(self):
        logging.info("[TTS] 启动 TTS 工作线程")
        if not self._session:
            self._session = aiohttp.ClientSession()
        self._running = True
        self._worker_task = asyncio.create_task(self.tts_worker())

    async def stop_worker(self):
        logging.info("[TTS] 停止 TTS 工作线程")
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._worker_task
        self._worker_task = None

    async def close(self):
        await self.stop_worker()
        if self._session:
            await self._session.close()
        self._session = None
        if self._q_buffer:
            self._q_buffer.close()
            self._q_buffer.deleteLater()
            self._q_buffer = None
        self._q_data = None

    async def _play_audio(self, audio_data: bytes):
        if self._q_buffer:
            self._q_buffer.close()
            self._q_buffer.deleteLater()

        self._q_data = QByteArray(audio_data)
        self._q_buffer = QBuffer(self)
        self._q_buffer.setData(self._q_data)

        if self._q_buffer.open(QIODeviceBase.OpenModeFlag.ReadOnly):
            self._q_buffer.seek(0)
            self.player.setSourceDevice(self._q_buffer, QUrl("audio.wav"))

            self.player.play()

            # 刚 play() 时状态是 Stopped，必须给它一点时间跳变到 Playing
            # 等待状态改变，或者等待一小段时间
            retry_count = 0
            while self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState and retry_count < 10:
                await asyncio.sleep(0.05)
                retry_count += 1

            # 进入阻塞循环
            while self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                await asyncio.sleep(0.1)
        else:
            logging.error("无法打开 QBuffer 进行读取")

    def tts_queue_put(self, text: str):
        if self.tts_queue.qsize() >= self.config.max_queue_size:
            try:
                self.tts_queue.get_nowait()
                self.tts_queue.task_done()
            except asyncio.QueueEmpty:
                pass
        self.tts_queue.put_nowait(text)

    async def tts_worker(self):
        """TTS 工作线程，子类必须实现"""
        pass


def get_name(full_name: str) -> str:
    match = re.search(r".*(?=-)", full_name)
    name = ""
    if match:
        name += match.group()
    else:
        raise AIClientException("模型名提取失败")
    return name


class AITTSClient(TTSClient):
    def __init__(self, conf_dict: dict):
        super().__init__(conf_dict)
        self.config: TTSClientConfig = TTSClientConfig(conf_dict)
        self.ai_config = AIClientConfig(conf_dict)
        self._weights: dict[str, AIWeightsPaths] = defaultdict()

    @property
    def weights_names(self) -> list[str]:
        return list(self._weights.keys())

    @override
    async def tts_worker(self):
        while self._running:
            if not self.weights_names:
                await asyncio.sleep(1)
                continue
            text = await self.tts_queue.get()
            try:
                logging.info(f"[TTS][AI] {text}")
                target_url = URL(self.ai_config.api_url) / "tts"

                if self._session.closed:
                    self._session = aiohttp.ClientSession()

                post_data = self.ai_config.post_req(text)
                # 发送 POST 请求并流式读取响应
                await self._post_tts(target_url, post_data)

            except Exception as e:
                ex = AIClientException(e)
                logging.error(ex)
            finally:
                self.tts_queue.task_done()

    def _find_ref_audio(self, name: str) -> str:
        audio_root = self.ai_config.ref_audio_root
        audio_path = None
        for path in audio_root.glob(f"{name}"):
            logging.info(f"[TTS][AI] 搜索{path.stem}的示例音频")
            audio_path = path / "reference_audios" / "中文" / "emotions"
            break
        if not audio_path or not audio_path.exists():
            raise AIClientException(f"未找到模型 {name} 的参考音频文件夹")
        audio = None
        for path in audio_path.glob("*.wav"):
            logging.info(f"[TTS][AI] 找到模型 {name} 的示例音频: {path.name}")
            audio = path
            break
        if not audio or not audio.exists():
            raise AIClientException(f"未找到模型 {name} 的参考音频文件")
        return str(audio)

    async def switch_weights(self, name: str) -> bool:
        try:
            if name not in self._weights:
                raise AIClientException(f"不存在名为 {name} 的模型文件")
            paths = self._weights[name]
            gpt_success = await self._request_switch_weights("set_gpt_weights", paths.gpt_path)
            sovits_success = await self._request_switch_weights("set_sovits_weights", paths.sovits_path)
            if gpt_success and sovits_success:
                self.ai_config.ref_audio_path = paths.ref_audio_path
                return True
            raise AIClientException("访问失败")
        except Exception as e:
            ex = AIClientException(f"切换模型文件失败: {e}")
            logging.error(ex)
            return False

    async def _request_switch_weights(self, endpoint: str, path: str) -> bool:
        logging.info("[TTS][AI] 切换模型文件: " + path)
        if self._is_test:
            return True
        self._is_test = True
        params = {"weights_path": path}
        target_url = (URL(self.ai_config.api_url) / endpoint).with_query(params)
        async with self._session.get(target_url) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("message") == "success":
                    return True
            else:
                data = await resp.json()
                logging.error(AIClientException(data["message"]))
            return False

    def _search_gpt_weights(self, gpt_root, sovits_root):
        for gpt_file_path in gpt_root.glob("*.ckpt"):
            name: str = get_name(gpt_file_path.stem)
            sovits_file_path = None
            logging.info(f"[TTS][AI] 找到模型文件: {gpt_file_path.name}，正在寻找对应的 SoVits 权重文件...")
            for path in sovits_root.glob(f"{name}*.pth"):
                logging.info(f"[TTS][AI] 找到模型文件: {gpt_file_path.name} 和 {path.name}")
                sovits_file_path = path
            if sovits_file_path is not None and sovits_file_path.exists():
                try:
                    self._weights[name] = AIWeightsPaths(
                        gpt_path=str(gpt_file_path),
                        sovits_path=str(sovits_file_path),
                        ref_audio_path=self._find_ref_audio(name)
                    )
                except Exception as e:
                    logging.error(f"模型 {name} 的不存在示例语音，已跳过: {e}")
                    continue
            else:
                logging.warning(f"未找到与 {gpt_file_path.name} 对应的 SoVits 权重文件，已跳过")


    async def scan_weights(self):
        self._weights.clear()
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        root = self.ai_config.gpt_sovits_root
        gpt_root = root / f"GPT_weights_{self.ai_config.version}" if self.ai_config.version != "v1" else "GPT_weights"
        sovits_root = root / f"SoVITS_weights_{self.ai_config.version}" if self.ai_config.version != "v1" else "SoVITS_weights"
        try:
            self._search_gpt_weights(gpt_root, sovits_root)
            if not self._weights:
                raise AIClientException("未找到任何有效的 GPT-SoVits 模型文件，请检查配置路径是否正确")
            else:
                default_weights = self.weights_names[0]
                if not await self.switch_weights(default_weights):
                    raise AIClientException(f"默认模型设置失败: {default_weights}")
        except Exception as e:
            ex = AIClientException(f"扫描模型文件失败: {e}")
            logging.error(ex)
            raise ex
