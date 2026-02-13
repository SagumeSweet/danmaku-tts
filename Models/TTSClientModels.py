from pathlib import PurePath, Path

from Enums import DefaultConfigName


class TTSClientConfig:
    def __init__(self, tts_client_config: dict):
        self._max_queue_size: int = tts_client_config[DefaultConfigName.max_queue_size]

    @property
    def max_queue_size(self) -> int:
        return self._max_queue_size

    @max_queue_size.setter
    def max_queue_size(self, max_queue_size: int):
        if not (isinstance(max_queue_size, int) or max_queue_size < 1):
            raise ValueError()
        self._max_queue_size = max_queue_size


class AIClientConfig:
    def __init__(self, tts_client_config: dict):
        self._api_url: str = tts_client_config[DefaultConfigName.ai][DefaultConfigName.api_url]
        self._ref_audio_root: str = tts_client_config[DefaultConfigName.ai][DefaultConfigName.ref_audio_root]
        self._prompt_lang: str = tts_client_config[DefaultConfigName.ai][DefaultConfigName.prompt_lang]
        self._gpt_sovits_root: str = tts_client_config[DefaultConfigName.ai][DefaultConfigName.gs_root]
        self._version = "v4"
        self._target_lang = "zh"
        self._ref_audio_path: str = ""

    @property
    def api_url(self) -> str:
        return self._api_url

    @property
    def ref_audio_root(self) -> Path:
        return Path(self._ref_audio_root) / self._version

    @property
    def prompt_lang(self) -> str:
        return self._prompt_lang

    @property
    def ref_audio_path(self) -> str:
        if not self._ref_audio_path:
            raise ValueError("ref_audio_path 未设置")
        return self._ref_audio_path

    @property
    def prompt_text(self) -> str:
        if not self._ref_audio_path:
            raise ValueError("ref_audio_path 未设置")
        text = PurePath(self._ref_audio_path).stem[5:]
        return text

    @property
    def version(self) -> str:
        return self._version

    @property
    def target_lang(self) -> str:
        return self._target_lang

    @property
    def gpt_sovits_root(self) -> Path:
        return Path(self._gpt_sovits_root)

    @ref_audio_path.setter
    def ref_audio_path(self, ref_audio_path: str):
        self._ref_audio_path = ref_audio_path

    @target_lang.setter
    def target_lang(self, target_lang: str):
        if target_lang not in ["zh", "en", "jp"]:
            raise ValueError()
        self._target_lang = target_lang

    @version.setter
    def version(self, version: str):
        if version not in ["v1", "v2", "v2Pro", "v2ProPlus", "v3", "v4"]:
            raise ValueError()
        self._version = version

    def post_req(self, text: str) -> dict:
        req = {
            "text": text,
            "text_lang": self.target_lang,
            "ref_audio_path": self.ref_audio_path,
            "prompt_text": self.prompt_text,
            "prompt_lang": self.prompt_lang,
            "text_split_method": "cut5",
            "media_type": "wav",
            "streaming_mode": False
        }
        return req


class AIWeightsPaths:
    def __init__(self, gpt_path: str, sovits_path: str, ref_audio_path: str):
        self._gpt_path = gpt_path
        self._sovits_path = sovits_path
        self._ref_audio_path = ref_audio_path

    @property
    def gpt_path(self) -> str:
        return self._gpt_path

    @property
    def sovits_path(self) -> str:
        return self._sovits_path

    @property
    def ref_audio_path(self) -> str:
        return self._ref_audio_path
