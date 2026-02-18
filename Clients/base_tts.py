import asyncio
import logging
from contextlib import suppress

from PySide6.QtCore import QUrl, QBuffer, QObject, QIODeviceBase, QByteArray
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from Models import TTSClientConfig


class BaseTTSClient(QObject):
    def __init__(self, config):
        super().__init__()
        self.config = TTSClientConfig(config)
        self.tts_queue = asyncio.Queue(self.config.max_queue_size)

        # 核心控制器：使用 Event 确保线程安全
        self._stop_event = asyncio.Event()
        self._worker_task = None

        # 播放器组件
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self._q_buffer = None

    def start(self):
        if self._worker_task and not self._worker_task.done():
            return
        self._stop_event.clear()
        self._worker_task = asyncio.create_task(self._tts_worker_loop())
        logging.info(f"[{self.__class__.__name__}] Worker started.")

    async def stop(self):
        self._stop_event.set()
        if self._worker_task:
            self._worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._worker_task
        logging.info(f"[{self.__class__.__name__}] Worker stopped.")

    async def close(self):
        await self.stop()
        self._worker_task = None

    async def _tts_worker_loop(self):
        """标准生产者-消费者循环"""
        try:
            while not self._stop_event.is_set():
                text = await self.tts_queue.get()
                try:
                    # 具体的子类实现如何获取音频
                    audio_bytes = await self.generate_audio(text)
                    if audio_bytes:
                        await self._play_audio_logic(audio_bytes)
                except Exception as e:
                    logging.error(f"Error processing TTS: {e}")
                finally:
                    self.tts_queue.task_done()
        except asyncio.CancelledError:
            logging.debug("TTS Worker task cancelled.")
            raise

    async def _play_audio_logic(self, data: bytes):
        """封装 Qt 播放逻辑，支持异步挂起直到播放结束"""
        if self._q_buffer:
            self._q_buffer.close()
            self._q_buffer.deleteLater()

        q_data = QByteArray(data)
        self._q_buffer = QBuffer(self)
        self._q_buffer.setData(q_data)

        if self._q_buffer.open(QIODeviceBase.OpenModeFlag.ReadOnly):
            self.player.setSourceDevice(self._q_buffer, QUrl("audio.wav"))
            self.player.play()

            # 状态同步：等待播放开始再到结束
            while self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                await asyncio.sleep(0.05)  # 极短等待启动

            while self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                await asyncio.sleep(0.1)  # 挂起协程直到播完
        else:
            logging.error("Failed to open QBuffer")

    async def generate_audio(self, text: str) -> bytes:
        """接口方法，子类必须实现"""
        raise NotImplementedError
