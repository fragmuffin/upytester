__all__ = [
    'instruction',
    'interpret',
    'get_sender',
    'send',
    'remote',
    'get_obj',
    'listener',
]

import gc as _gc
from .mapping import instruction, send
_gc.collect()
from .mapping import remote, get_obj
_gc.collect()
from .process import listener, interpret
_gc.collect()

# Import all sub-modules (forces instructions to register)
from . import system
_gc.collect()
from . import test
_gc.collect()
from . import io
_gc.collect()
from . import leds
_gc.collect()
from . import can
_gc.collect()
from . import spi
_gc.collect()
