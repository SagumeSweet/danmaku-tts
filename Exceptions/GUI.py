class GUIException(Exception):
    """Base class for GUI-related exceptions."""
    def __init__(self, message="GUI 错误"):
        full_message = f"[GUI]{message}"
        super().__init__(full_message)

class ManagerCardException(GUIException):
    """Base class for ManagerCard-related exceptions."""
    def __init__(self, message="ManagerCard 错误"):
        full_message = f"[ManagerCard]{message}"
        super().__init__(full_message)