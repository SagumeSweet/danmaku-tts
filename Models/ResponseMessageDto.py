class DanmakuResponseMessage:
    def __init__(self, res_msg: dict):
        self._badge_name: str = res_msg['badgeName']
        self._badge_level: int = res_msg['badgeLevel']
        self._content: str = res_msg['content']
        self._username: str = res_msg['username']
        self._user_avatar: str = res_msg['userAvatar']

    @property
    def badge_name(self) -> str:
        return self._badge_name

    @property
    def badge_level(self) -> int:
        return self._badge_level

    @property
    def content(self) -> str:
        return self._content

    @property
    def username(self) -> str:
        return self._username


class ResponseMessageDto:
    def __init__(self, msg_dto: dict):
        self._platform: str = msg_dto['platform']
        self._room_id: str = msg_dto['roomId']
        self._type: str = msg_dto['type']
        self._msg: DanmakuResponseMessage = DanmakuResponseMessage(msg_dto["msg"])

    @property
    def platform(self) -> str:
        return self._platform

    @property
    def room_id(self) -> str:
        return self._room_id

    @property
    def type(self) -> str:
        return self._type

    @property
    def msg(self) -> DanmakuResponseMessage:
        return self._msg
