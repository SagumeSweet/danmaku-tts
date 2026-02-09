from pathlib import Path


class TTSClientConfig:
    def __init__(self):
        self._api_url: str = "http://localhost:9880/tts"
        self._ref_audio_path: str = r"E:\program\GPT-SoVITS-v2pro-20250604\声音模型\v4\莫娜_ZH\reference_audios\中文\emotions\【默认】但我从来没见过她，而且她如果还活着，岁数也绝对不小了…老太婆都有好几百岁，她比老太婆还长寿呢！.wav"
        self._prompt_lang: str = "zh"
        self._target_lang: str = "zh"
        self._max_queue_size: int = 5

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
