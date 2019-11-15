__all__ = [
    'instruction',
    'interpret',
    'get_sender',
    'send',
    'remote',
    'get_obj',
    'listener',
]


from .mapping import instruction, send
from .mapping import remote, get_obj
from .process import listener, interpret

# Import all sub-modules (forces instructions to register)
from . import system
from . import test
from . import io
from . import leds
from . import can
from . import spi
