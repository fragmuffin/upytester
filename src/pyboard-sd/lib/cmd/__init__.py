__all__ = [
    'instruction',
    'interpret',
    'get_sender',
]


from .mapping import instruction, interpret, get_sender

# Import all sub-modules (forces instructions to register)
from . import system
from . import test
from . import io
from . import can
from . import spi
