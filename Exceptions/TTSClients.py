class TTSClientException(Exception):
    """Base exception class for TTS client errors."""
    def __init__(self, message="配置项缺失或错误"):
        # 包装错误信息：加上具体的键名
        full_message = f"[TTS]{message}"
        super().__init__(full_message)

class AIClientException(TTSClientException):
    """Base exception class for AIClient errors."""
    def __init__(self, message="AI TTS 配置项缺失或错误"):
        full_message = f"[AI]{message}"
        super().__init__(full_message)
