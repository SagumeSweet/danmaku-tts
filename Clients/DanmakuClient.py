import asyncio
import json
import logging
from datetime import timedelta
from asyncio import Event
import aiohttp
from rsocket.helpers import single_transport_provider
from rsocket.payload import Payload
from rsocket.rsocket_client import RSocketClient
from rsocket.streams.stream_from_async_generator import StreamFromAsyncGenerator
from rsocket.transports.aiohttp_websocket import TransportAioHttpClient
from PySide6.QtCore import QObject, Signal

from Exceptions import DanmakuClientException, RsocketClientException
from Models import ResponseMessageDto, DanmakuClientConfig


class DanmakuClient(QObject):
    danmu_received = Signal(ResponseMessageDto)
    status_changed = Signal(str)

    def __init__(self, danmaku_config: dict):
        super().__init__()
        self._config = DanmakuClientConfig(danmaku_config)
        self._worker_task = None
        self._stop_event = Event()

    @property
    def subscribe_data(self) -> dict:
        subscribe_data = {
            "data": {
                "taskIds": self._config.task_ids,
                "cmd": "SUBSCRIBE"
            }
        }
        return subscribe_data

    async def start(self):
        """启动客户端任务"""
        if self._worker_task is None or self._worker_task.done():
            self._stop_event.clear()
            self._worker_task = asyncio.create_task(self._rsocket_worker())
            logging.info("[DanmakuClient] DanmakuClient 已启动任务")

    async def stop(self):
        """停止客户端并清理资源"""
        if self._worker_task:
            logging.info("[DanmakuClient] 正在停止 DanmakuClient...")
            self._stop_event.set()  # 通知 worker 停止
            try:
                await asyncio.wait_for(self._worker_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._worker_task.cancel()
            self._worker_task = None
            self.status_changed.emit("已断开")
            logging.info("[DanmakuClient] DanmakuClient 已停止")

    async def _rsocket_worker(self):
        """核心连接循环"""
        while not self._stop_event.is_set():
            try:
                self.status_changed.emit("正在连接...")
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(self._config.websocket_url) as websocket:
                        transport = TransportAioHttpClient(websocket=websocket)
                        async with RSocketClient(
                                single_transport_provider(transport),
                                keep_alive_period=timedelta(seconds=30),
                                max_lifetime_period=timedelta(days=1)
                        ) as client:
                            self.status_changed.emit("已连接")

                            # 通道建立逻辑
                            channel_completion_event = Event()

                            async def generator():
                                yield Payload(data=json.dumps(self.subscribe_data["data"]).encode()), False
                                # 等待停止信号或频道结束
                                await self._stop_event.wait()

                            stream = StreamFromAsyncGenerator(generator)
                            requested = client.request_channel(Payload(), stream)

                            # 传入自身用于回调
                            subscriber = InternalSubscriber(channel_completion_event, self)
                            requested.subscribe(subscriber)

                            # 持续运行直到事件触发
                            await asyncio.wait(
                                [asyncio.create_task(channel_completion_event.wait()),
                                 asyncio.create_task(self._stop_event.wait())],
                                return_when=asyncio.FIRST_COMPLETED
                            )

            except Exception as e:
                ex = RsocketClientException(e)
                logging.error(f"连接异常： {ex}")
                self.status_changed.emit("连接异常，重试中...")
                await asyncio.sleep(5)  # 失败重试间隔


# 内部订阅者类
from reactivestreams.subscriber import Subscriber
from reactivestreams.subscription import Subscription


class InternalSubscriber(Subscriber):
    def __init__(self, completion_event, client: DanmakuClient) -> None:
        super().__init__()
        self._completion_event = completion_event
        self._client = client

    def on_subscribe(self, subscription: Subscription):
        subscription.request(0x7FFFFFFF)

    def on_next(self, value: Payload, is_complete=False):
        try:
            res = json.loads(value.data)
            if isinstance(res, dict) and res.get('type') == "DANMU":
                msg_dto: ResponseMessageDto = ResponseMessageDto(res)
                self._client.danmu_received.emit(msg_dto)
        except Exception as e:
            ex = DanmakuClientException(e)
            logging.error(f"解析弹幕数据失败: {ex}")

        if is_complete:
            self._completion_event.set()

    def on_error(self, exception: Exception):
        self._completion_event.set()

    def on_complete(self):
        self._completion_event.set()
