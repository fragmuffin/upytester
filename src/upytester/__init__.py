# ------- Package Meta Data
__version__ = "0.1.dev1"

__title__ = 'upytester'
__description__ = 'Hardware test environment using MicroPython hardware as an interface'
__url__ = 'https://github.com/fragmuffin/upytester'

__author__ = 'Peter Boin'
__email__ = 'peter.boin+upytester@gmail.com'

__license__ = 'MIT'

__keywords__ = ['micropython', 'pyboard', 'testing', 'unittest', 'hardware']

# ------- Imports
__all__ = [
    'PyBoard',

    # sub-modules
    'project',
    'pyboard',
]

from .pyboard import PyBoard

# sub-modules
from . import project
from . import pyboard
