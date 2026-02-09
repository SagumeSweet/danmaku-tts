import asyncio

import aiohttp
import logging

from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QBuffer, QObject, QIODeviceBase, QByteArray

from Models import TTSClientConfig


class TTSClient(QObject):
    def __init__(self, config: TTSClientConfig):
        super().__init__()
        self.config: TTSClientConfig = config
        self._tts_queue = asyncio.Queue()

        # 初始化 Qt 播放器
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        self._q_data = None
        self._q_buffer = None

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

    async def ai_tts_worker(self):
        async with aiohttp.ClientSession() as session:
            while True:
                text = await self._tts_queue.get()
                try:
                    logging.info(f"[AI 合成中] {text}")
                    post_data = {
                        "text": text,
                        "text_lang": self.config.target_lang,
                        "ref_audio_path": self.config.ref_audio_path,
                        "prompt_text": self.config.prompt_text,
                        "prompt_lang": self.config.prompt_lang,
                        "text_split_method": "cut5",
                        "media_type": "wav",
                        "streaming_mode": False,
                        "speed_factor": 1.3
                    }
                    # 发送 POST 请求并流式读取响应
                    async with session.post(self.config.api_url, json=post_data) as resp:
                        if resp.status == 200:
                            logging.debug("成功接收生成语音")
                            audio_data = await resp.read()
                            await self._play_audio(audio_data)
                except Exception as e:
                    logging.error(f"[TTS 异常] {e}")
                finally:
                    self._tts_queue.task_done()

    def tts_queue_put(self, text: str):
        if self._tts_queue.qsize() >= self.config.max_queue_size:
            try:
                self._tts_queue.get_nowait()
                self._tts_queue.task_done()
            except asyncio.QueueEmpty:
                pass
        self._tts_queue.put_nowait(text)
