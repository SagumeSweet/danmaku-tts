from Enums import DefaultConfigName


class DanmakuClientConfig:
    def __init__(self, config: dict):
        self._websocket_url = config[DefaultConfigName.rsocket_ws_url]
        self._task_ids = config[DefaultConfigName.task_ids]

    @property
    def websocket_url(self) -> str:
        return self._websocket_url

    @property
    def task_ids(self) -> list[str]:
        return self._task_ids.copy()