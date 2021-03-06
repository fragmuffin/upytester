__all__ = [
    'connected_serial_numbers',
    'find_portinfo',

    # Storage Functions : SD card
    'find_mountpoint_sd',
    'mount_sd',
    'unmount_sd',
    'sync_files_to_sd',

    # Storage Functions : Flash
    'find_mountpoint_flash',
    'mount_flash',
    'unmount_flash',
    'sync_files_to_flash',
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
