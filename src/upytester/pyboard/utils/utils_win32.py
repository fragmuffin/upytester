# FIXME: Experimental Code
#   As of writing this, most of this module's code was written in an attempt
#   to get a reliable working system on Windows 10.
#   The challenge was in mapping:
#       serial_number -> comport (eg: 'COM3')
#       serial_number -> mountpoint (eg: 'D:\')
import os
import sys
if not os.path.basename(sys.argv[0]).startswith('sphinx'):
    raise NotImplementedError("Windows not supported, yet")
    import winreg
# ref: https://github.com/fragmuffin/upytester/issues/2

import re
import serial
import itertools


# ---- winreg utilities -----
def _EnumKey_iter(key):
    for i in itertools.count():
        try:
            yield winreg.EnumKey(key, i)
        except OSError:
            break


def _pyboard_serial_number(port):
    port_match = re.search(r'^\d+-((?P<hub>\d+).)?(?P<port>\d+):', port.location)

    group_equal = lambda m1, m2, k: int(m1.group(k)) == int(m2.group(k))

    # Pull the device serial from windows registry
    import winreg
    key_path = r'SYSTEM\ControlSet001\Enum\USB\VID_{VID:X}&PID_{PID:X}'.format(
        VID=port.vid,
        PID=port.pid,
    )
    usb_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
    for name in _EnumKey_iter(usb_key):
        # Registry USB Location
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, '{}\\{}'.format(key_path, name))
        location_info = winreg.QueryValueEx(key, 'LocationInformation')[0]
        reg_match = re.search(r'^Port_#(?P<port>\d+)\.Hub_#(?P<hub>\d+)', location_info)
        if group_equal(port_match, reg_match, 'hub') and group_equal(port_match, reg_match, 'port'):
            return name

    raise ValueError("Could not find pyboard for port {}".format(port.usb_info()))


def _pyboard_mounted_sd(serial_number):
    # IMPORTANT:
    #   registry will show last mounted location, so before syncing
    #   to device, make sure it's connected.
    #   note: if comport exists, then it's connected ;)
    import winreg
    parent_key = winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        r'SOFTWARE\Microsoft\Windows Portable Devices\Devices'
    )
    for name in _EnumKey_iter(parent_key):
        # example sub_key name
        #  SWD#WPDBUSENUM#_??_USBSTOR#DISK&VEN_UPY&PROD_MICROSD_SD_CARD&REV_1.00#7&2CF2AA75&0&3976346C3436&0#{53F56307-B6BF-11D0-94F2-00A0C91EFB8B}
        split_name = name.split('&')
        if all((k in split_name) for k in [serial_number, 'VEN_UPY', 'PROD_MICROSD_SD_CARD']):
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r'SOFTWARE\Microsoft\Windows Portable Devices\Devices\{}'.format(name)
            )
            return winreg.QueryValueEx(key, 'FriendlyName')[0]


def get_pyboard_map(refresh=False):
    """
    Get a dict mapping pyboard serial numbers to the connected
    serial ports, and mount-points.

    Return Example::

        >>> get_pyboard_map()
        {
            '3976346C3436': {
                'port': <serial.tools.list_ports_common.ListPortInfo at 0x20a82202be1>,
                'mount': 'G:\\'
            }
        }

    :param refresh: If ``True``, the OS is interrogated and replaces any
                    previous map
    :type refresh: :class:`bool`
    :param clean: Clear cache before processing request (default: ``False``)
    :type clean: :class:`bool`
    """
    map = {}
    from serial.tools.list_ports import comports
    for port in comports():
        serial_number = _pyboard_serial_number(port)
        if serial_number:
            # (serial_number, port)
            map[serial_number] = {
                'port': port,
                'mount': _pyboard_mounted_sd(serial_number),
            }

    return map


def sync_path_to_sd(source_path, pyboard):
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

    CHECK_FILES = ['main.py', '.pyboard-sd']
    if not all(os.path.exists(os.path.join(mountpoint, f)) for f in CHECK_FILES):
        raise ValueError(
            (
                "mountpoint does not contain {files} file(s), are you sure you "
                "want to overwrite everything on that drive? manually create "
                "files with these names to the SD card if you wish to continue."
            ).format(
                files=', '.join(CHECK_FILES)
            )
        )

    # Create & Run process
    process = subprocess.Popen(
        [
            'Robocopy.exe',
            os.path.abspath(source_path),
            os.path.abspath(mountpoint),
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
