import asyncio

from .base_tts import BaseTTSClient


class EdgeTTSClient(BaseTTSClient):
    async def generate_audio(self, text: str) -> bytes:
        await asyncio.sleep(3)
        raise NotImplementedError("Edge TTS client is not implemented yet.")
