__all__ = [
    'instruction',
    'interpret',
    'get_sender',
    'send',
    'remote',
]


from .mapping import instruction, interpret, send, remote

# Import all sub-modules (forces instructions to register)
from . import system
from . import test
from . import io
from . import leds
from . import can
from . import spi
