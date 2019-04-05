__all__ = [
    'find_comport',
    'find_mountpoint_sd',
    'mount_sd',
    'unmount_sd',
    'sync_path_to_sd',
]

# Import platform's utils module
import sys
import importlib

platform = sys.platform
if platform.startswith('linux'):
    platform = 'linux'  # python 2/3 thing

utils = importlib.import_module('.utils_' + platform, __name__)
for name in __all__:
    globals()[name] = getattr(utils, name)
