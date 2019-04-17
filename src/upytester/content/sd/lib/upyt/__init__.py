__all__ = [
    'cmd',
    'utils',
    'sched',
]

# Only load by pyboard
import sys
if sys.platform != 'pyboard':
    # Why?: The upytester platform can be a bit confusing, particularly because
    #       this module is stored within a sub-folder of the upytester library
    #       on the host.
    import os
    if not os.path.basename(sys.argv[0]).startswith('sphinx'):
        # If a sphinx build is attempting to import, well that's ok.
        raise AssertionError("module target must be a pyboard")

# Import Sub-modules
from . import cmd
from . import utils
from . import sched
