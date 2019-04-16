__all__ = [
    'instruction',
    'interpret',
    'get_sender',
    'send',
]


from .mapping import instruction, interpret, set_serial_port, send

# Import all sub-modules (forces instructions to register)
from . import system
from . import test
from . import io
from . import leds
from . import can
from . import spi
