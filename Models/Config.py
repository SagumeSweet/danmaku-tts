from Enums import DefaultConfigName


class Config:
    def __init__(self, config: dict):
        self._danmaku_client = config.get(DefaultConfigName.danmaku_client, {})
        self._tts_client = config.get(DefaultConfigName.ttl_client, {})

    @property
    def danmaku_client(self) -> dict:
        return self._danmaku_client

    @property
    def tts_client(self) -> dict:
        return self._tts_client