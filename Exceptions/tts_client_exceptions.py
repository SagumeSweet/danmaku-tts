class TTSException(Exception):
    """Base exception class for TTS client errors."""
    def __init__(self, message="配置项缺失或错误"):
        # 包装错误信息：加上具体的键名
        full_message = f"[TTS]{message}"
        super().__init__(full_message)

class TTSPlaybackException(TTSException):
    """播放器或缓冲区相关错误"""
    pass

class TTSNetworkException(TTSException):
    """网络请求或后端服务错误"""
    pass

class AITTSException(TTSException):
    """Base exception class for AIClient errors."""
    def __init__(self, message="error"):
        full_message = f"[AI]{message}"
        super().__init__(full_message)

class EdgeTTSException(TTSException):
    """Base exception class for EdgeTTSClient errors."""
    def __init__(self, message="error"):
        full_message = f"[Edge]{message}"
        super().__init__(full_message)
