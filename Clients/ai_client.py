import asyncio
import logging
import re
from collections import defaultdict
from typing import override

import aiohttp
from yarl import URL

from Exceptions import AITTSException
from Models import AIWeightsPaths, AIClientConfig
from .base_tts import BaseTTSClient


def get_name(full_name: str) -> str:
    match = re.search(r".*(?=-)", full_name)
    name = ""
    if match:
        name += match.group()
    else:
        raise AITTSException("模型名提取失败")
    return name


class AITTSClient(BaseTTSClient):
    def __init__(self, config):
        super().__init__(config)
        self._session = None
        self.ai_config = AIClientConfig(config)
        self._weights: dict[str, AIWeightsPaths] = defaultdict()

    @property
    def weights_names(self) -> list[str]:
        return list(self._weights.keys())

    def _set_target_lang(self, text: str):
        if any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):
            self.ai_config.target_lang = "auto"
        else:
            self.ai_config.target_lang = "zh"

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    @override
    async def generate_audio(self, text: str) -> bytes:
        if not self.weights_names:
            await asyncio.sleep(1)
            raise AITTSException("没有可用的模型权重")
        session = await self._get_session()
        api_url = URL(self.ai_config.api_url) / "tts"
        self._set_target_lang(text)

        # 构造请求
        post_data = self.ai_config.post_req(text)

        async with session.post(api_url, json=post_data) as resp:
            if resp.status == 200:
                return await resp.read()
            else:
                ex = AITTSException(f"AI TTS Server error: {resp.status}")
                raise ex

    @override
    async def close(self):
        await super().stop()
        if self._session:
            await self._session.close()

    def _find_ref_audio(self, name: str) -> str:
        audio_root = self.ai_config.ref_audio_root
        audio_path = None
        for path in audio_root.glob(f"{name}"):
            logging.info(f"[TTS][AI] 搜索{path.stem}的示例音频")
            audio_path = path
            break
        if not audio_path or not audio_path.exists():
            raise AITTSException(f"未找到模型 {name} 的参考音频文件夹")
        audio = None
        for path in audio_path.rglob("*.wav"):
            logging.info(f"[TTS][AI] 找到模型 {name} 的示例音频: {path.name}")
            audio = path
            break
        if not audio or not audio.exists():
            raise AITTSException(f"未找到模型 {name} 的参考音频文件")
        return str(audio)

    async def switch_weights(self, name: str) -> bool:
        try:
            if name not in self._weights:
                raise AITTSException(f"不存在名为 {name} 的模型文件")
            paths = self._weights[name]
            gpt_success = await self._request_switch_weights("set_gpt_weights", paths.gpt_path)
            sovits_success = await self._request_switch_weights("set_sovits_weights", paths.sovits_path)
            if gpt_success and sovits_success:
                self.ai_config.ref_audio_path = paths.ref_audio_path
                return True
            raise AITTSException("访问失败")
        except Exception as e:
            ex = AITTSException(f"切换模型文件失败: {e}")
            logging.error(ex)
            return False

    async def _request_switch_weights(self, endpoint: str, path: str) -> bool:
        logging.info("[TTS][AI] 切换模型文件: " + path)
        self._is_test = True
        params = {"weights_path": path}
        target_url = (URL(self.ai_config.api_url) / endpoint).with_query(params)
        session = await self._get_session()
        async with session.get(target_url) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("message") == "success":
                    return True
            else:
                data = await resp.json()
                logging.error(AITTSException(data["message"]))
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
        root = self.ai_config.gpt_sovits_root
        gpt_root = root / f"GPT_weights_{self.ai_config.version}" if self.ai_config.version != "v1" else "GPT_weights"
        sovits_root = root / f"SoVITS_weights_{self.ai_config.version}" if self.ai_config.version != "v1" else "SoVITS_weights"
        try:
            self._search_gpt_weights(gpt_root, sovits_root)
            if not self._weights:
                raise AITTSException("未找到任何有效的 GPT-SoVits 模型文件，请检查配置路径是否正确")
            else:
                default_weights = self.weights_names[0]
                if not await self.switch_weights(default_weights):
                    raise AITTSException(f"默认模型设置失败: {default_weights}")
        except Exception as e:
            ex = AITTSException(e)
            logging.error(ex)
            raise ex

