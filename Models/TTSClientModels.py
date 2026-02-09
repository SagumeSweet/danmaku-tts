from pathlib import Path

from Enums import DefaultConfigName


class TTSClientConfig:
    def __init__(self, tts_client_config: dict):
        self._api_url: str = tts_client_config[DefaultConfigName.ai][DefaultConfigName.api_url]
        self._ref_audio_path: str = tts_client_config[DefaultConfigName.ai][DefaultConfigName.ref_audio_path]
        self._prompt_lang: str = tts_client_config[DefaultConfigName.ai][DefaultConfigName.prompt_lang]
        self._target_lang: str = tts_client_config[DefaultConfigName.ai][DefaultConfigName.target_lang]
        self._max_queue_size: int = tts_client_config[DefaultConfigName.ai][DefaultConfigName.max_queue_size]

    @property
    def api_url(self) -> str:
        return self._api_url

    @property
    def ref_audio_path(self) -> str:
        return self._ref_audio_path

    @property
    def prompt_text(self) -> str:
        text = Path(self._ref_audio_path).stem[5:]
        return text

    @property
    def prompt_lang(self) -> str:
        return self._prompt_lang

    @property
    def target_lang(self) -> str:
        return self._target_lang

    @property
    def max_queue_size(self) -> int:
        return self._max_queue_size

    @ref_audio_path.setter
    def ref_audio_path(self, path_str: str):
        path = Path(path_str)
        if path.is_file() and path.suffix == ".wav":
            self._ref_audio_path = path_str
        else:
            raise FileNotFoundError

    @target_lang.setter
    def target_lang(self, target_lang: str):
        if target_lang not in ["zh", "en", "jp"]:
            raise ValueError()
        self._target_lang = target_lang

    @max_queue_size.setter
    def max_queue_size(self, max_queue_size: int):
        if not (isinstance(max_queue_size, int) or max_queue_size < 1) :
            raise ValueError()
        self._max_queue_size = max_queue_size
