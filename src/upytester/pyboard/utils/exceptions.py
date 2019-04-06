class PyBoardNotFoundError(Exception):
    """Raised if the requested board could not be found"""

class DeviceFileNotFoundError(Exception):
    """Raised if the device-file associated with a pyboard could not be found"""
