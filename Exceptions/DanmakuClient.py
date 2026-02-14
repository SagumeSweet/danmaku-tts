class DanmakuClientException(Exception):
    """DanmakuClientException is the base class for all exceptions raised by DanmakuClient."""
    def __init__(self, message="DanmakuClient 错误"):
        full_message = f"[DanmakuClient]{message}"
        super().__init__(full_message)

class RsocketClientException(DanmakuClientException):
    """RsocketClientException is raised for errors related to the Rsocket client."""
    def __init__(self, message="RsocketClient 错误"):
        full_message = f"[RsocketClient]{message}"
        super().__init__(full_message)