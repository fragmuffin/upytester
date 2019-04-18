class ResponseTimeoutException(Exception):
    """Raised when no 'ok' response is received from the pyboard"""

class PyBoardError(Exception):
    """Raised in liue of an exception raised on a remote PyBoard"""
