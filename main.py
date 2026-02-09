import asyncio
import json
import logging
import sys

import aiohttp
from asyncio import Event
from contextlib import asynccontextmanager
from datetime import timedelta

from rsocket.helpers import single_transport_provider
from rsocket.payload import Payload
from rsocket.rsocket_client import RSocketClient
from rsocket.streams.stream_from_async_generator import StreamFromAsyncGenerator
from rsocket.transports.aiohttp_websocket import TransportAioHttpClient
from reactivestreams.subscriber import Subscriber
from reactivestreams.subscription import Subscription

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from Gui import MainConsole
from Models import ResponseMessageDto
from TTSClient import TTSClient

# 弹幕订阅 Payload
subscribe_payload_json = {"data": {"taskIds": [], "cmd": "SUBSCRIBE"}}


class ChannelSubscriber(Subscriber):
    def __init__(self, wait_for_responder_complete: Event, tts_client: TTSClient, console=None) -> None:
        super().__init__()
        self.subscription = None
        self._wait_for_responder_complete = wait_for_responder_complete
        self._tts_client = tts_client
        self._console = console

    def on_subscribe(self, subscription: Subscription):
        self.subscription = subscription
        self.subscription.request(0x7FFFFFFF)

    def on_next(self, value: Payload, is_complete=False):
        res = json.loads(value.data)
        if not isinstance(res, dict) or res.get('type') != "DANMU":
            return

        msg_dto: ResponseMessageDto = ResponseMessageDto(res)

        msg = msg_dto.msg
        nick = msg.username
        content = msg.content

        # 发送到弹幕面板
        if self._console and self._console.panel:
            self._console.panel.new_danmu_signal.emit(nick, content)

        # 文本预处理
        clean_txt = content[:40].replace('[', '').replace(']', '')
        speak_text = f"{nick}说，{clean_txt}"

        self._tts_client.tts_queue_put(speak_text)

        logging.info(f"[收到弹幕] {nick}: {content}")

        if is_complete:
            self._wait_for_responder_complete.set()

    def on_error(self, exception: Exception):
        self._wait_for_responder_complete.set()

    def on_complete(self):
        self._wait_for_responder_complete.set()


@asynccontextmanager
async def connect(websocket_uri):
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(websocket_uri) as websocket:
            async with RSocketClient(
                    single_transport_provider(TransportAioHttpClient(websocket=websocket)),
                    keep_alive_period=timedelta(seconds=30),
                    max_lifetime_period=timedelta(days=1)
            ) as client:
                yield client


async def rsocket_worker(websocket_uri, console, tts_client):
    """专门负责 RSocket 连接的异步任务"""
    try:
        async with connect(websocket_uri) as client:
            channel_completion_event = Event()

            async def generator():
                yield Payload(
                    data=json.dumps(subscribe_payload_json["data"]).encode()
                ), False
                await asyncio.Event().wait()

            stream = StreamFromAsyncGenerator(generator)
            requested = client.request_channel(Payload(), stream)

            # 传入 console 实例
            subscriber = ChannelSubscriber(channel_completion_event, tts_client, console=console)
            requested.subscribe(subscriber)

            await channel_completion_event.wait()
    except Exception as e:
        logging.error(f"RSocket 连接断开: {e}")


def main():
    # 1. 初始化日志和参数
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    rsocket_uri = "ws://localhost:39898"
    task_ids = ["2020489947524583424", "2020467538520133632", "2020466446579224576"]
    subscribe_payload_json["data"]["taskIds"] = task_ids

    # 2. 初始化 Qt + 异步事件循环
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 3. 启动 GUI
    console = MainConsole()
    console.show()

    # 4. 启动后台任务
    tts_client = TTSClient()
    loop.create_task(tts_client.ai_tts_worker())  # 启动 TTS
    loop.create_task(rsocket_worker(rsocket_uri, console, tts_client))  # 启动弹幕监听

    # 5. 进入循环
    with loop:
        loop.run_forever()


if __name__ == '__main__':
    main()
