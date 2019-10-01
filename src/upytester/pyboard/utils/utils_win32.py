# FIXME: Experimental Code
#   As of writing this, most of this module's code was written in an attempt
#   to get a reliable working system on Windows 10.
#   The challenge was in mapping:
#       serial_number -> comport (eg: 'COM3')
#       serial_number -> mountpoint (eg: 'D:\')
import os
import sys
if not os.path.basename(sys.argv[0]).startswith('sphinx'):
    #import winreg
    pass

import yaml

# ref: https://github.com/fragmuffin/upytester/issues/2

OVERRIDE_ENV_VAR = 'PYBOARD_CONFIG_FILE'

_override_dict = None

def _get_override_config():
    global _override_dict
    if _override_dict is None:
        filename = os.environ.get(OVERRIDE_ENV_VAR, None)
        if filename and os.path.isfile(filename):
            with open(filename, 'r') as fh:
                _override_dict = yaml.load(fh, Loader=yaml.FullLoader)
        else:
            _override_dict = {}

    return _override_dict


def connected_serial_numbers():
    overrides = _get_override_config()
    if overrides:
        return overrides.keys()
    else:
        raise NotImplemented("not implemented for win32")  # [issue #2]


def find_portinfo(pyboard):
    # --- All serial ports
    overrides = _get_override_config()
    if overrides:
        from serial.tools.list_ports import comports
        port_info_list = [
            c for c in comports()
            if c.device == overrides[pyboard.serial_number]['comport']
        ]
    else:
        raise NotImplemented("not implemented for win32")  # [issue #2]

    if not port_info_list:
        raise PyBoardNotFoundError("pyboard not found: '%s'" % pyboard.serial_number)
    elif len(port_info_list) > 1:
        raise PyBoardNotFoundError("multiple pyboards found: '%s'" % pyboard.serial_number)

    return port_info_list[0]


def find_mountpoint(pyboard):
    overrides = _get_override_config()
    if overrides:
        return overrides[pyboard.serial_number]['mountpoint']
    else:
        raise NotImplemented("not implemented for win32")  # [issue #2]


def mount(pyboard):
    overrides = _get_override_config()
    if overrides:
        # Assumption: assume it's already mounted
        mountpoint = overrides[pyboard.serial_number]['mountpoint']
        if not os.path.isdir(mountpoint):
            raise ValueError("{} drive for {!r} not mounted".format(mountpoint, pyboard))
        # TODO: how to mount device in windows?
    else:
        raise NotImplemented("not implemented for win32")  # [issue #2]


def unmount(pyboard):
    overrides = _get_override_config()
    if overrides:
        # Don't unmount... risk bad stuff happening
        pass
        # TODO: how to "eject" device in windows?
    else:
        raise NotImplemented("not implemented for win32")  # [issue #2]


def sync_files_to(source_path, pyboard, subdir='.', force=False, dryrun=False, quiet=False, exclude=[]):
    """
    :param source_path: Source folder to sync with SD card
    :type source_path: :class:`str`
    """
    # Validate Request
    if not os.path.isdir(source_path):
        raise ValueError(
            "given source_path '{}' does not exist (or is not a folder)".format(source_path)
        )

    mountpoint = pyboard.mountpoint_sd
    if not os.path.isdir(mountpoint):
        raise ValueError(
            "pyboard's mountpoint '{}' does not exist (or is not a folder)".format(mountpoint)
        )

    CHECK_FILES = ['.pyboard-sd', '.pyboard-flash']  # TODO: interchangable SD / Flash
    if not any(os.path.exists(os.path.join(mountpoint, f)) for f in CHECK_FILES):
        raise ValueError(
            (
                "mountpoint does not contain {files} file(s), are you sure you "
                "want to overwrite everything on that drive? manually create "
                "files with these names to the SD card if you wish to continue."
            ).format(
                files=', '.join(CHECK_FILES)
            )
        )

    # Create & Run sync process
    abs_source = os.path.abspath(source_path)
    abs_dest = os.path.abspath(os.path.join(mountpoint, subdir))

    assert os.path.relpath(abs_dest, 'C:\\') != '.', "destination is C: drive!!?"

    if not quiet:
        print("Synchronising files:")
        print("    - source: {!r}".format(abs_source))
        print("    - dest:   {!r}".format(abs_dest))

    # Create & Run process
    if not dryrun:
        process = subprocess.Popen(
            [
                'Robocopy.exe',
                abs_source, abs_dest,
                '/MIR', '/Z', '/W:5',
            ],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for line in process.stdout:
            process.poll()
            print(line.decode().rstrip('\n'))
        process.wait()


# Duplicate functions for SD and Flash.
# Assume they're both the same
#   (I know that doesn't make sense, but I'm sort of in a hurry)
from functools import wraps
for suffix in ('_sd', '_flash'):
    for func_name in ('find_mountpoint', 'mount', 'unmount', 'sync_files_to'):
        globals()['{}{}'.format(func_name, suffix)] = globals()[func_name]
