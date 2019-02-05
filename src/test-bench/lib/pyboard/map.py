import re
import sys
import serial
import serial.tools.list_ports_common
import itertools
import os

MAPFILE_ENVVAR = 'PYBOARD_MAP'


# --- Variable(s)
_cached_map = None


# ---- winreg utilities -----
def _EnumKey_iter(key):
    import winreg
    for i in itertools.count():
        try:
            yield winreg.EnumKey(key, i)
        except OSError:
            break


def _pyboard_serial_number(port):
    if sys.platform.startswith('win'):
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

    return port.serial_number


def _pyboard_mounted_sd(serial_number):
    if sys.platform.startswith('win'):
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

    else:  # assumed linux
        # bash equivalent
        #   device=$(ls /dev/disk/by-id/usb-uPy_microSD_SD_card_${serialnum}-*-part1)
        #   mountpoint=$(udisksctl info --block-device ${device} | grep MountPoints | sed 's/^.*:\s*//')
        raise NotImplemented("linux not supported (yet)")


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
    if MAPFILE_ENVVAR in os.environ:
        # I'm so very sick of windows and the registry, I've spent far
        # too much time trying to do this automatically (as you can see by
        # the rest of this file).
        # Windows is just a f**king mess, and I give up.
        def _get_map():
            import json
            with open(os.environ[MAPFILE_ENVVAR], 'r') as fh:
                mapfile = json.load(fh)
            # Format:
            #   {
            #       <usb-location>: {
            #           'serialnumber': <serial of device>,
            #           'mountpoint': '<drive letter>:\\',
            #
            #       }
            #
            #       # example:
            #       '1-1.1:x.1': {
            #           "serialnumber": "3373375E3037",
            #           "mountpoint": "D:\\",
            #       },
            #
            #   }
            #
            # To find srial port "location", plug 1 pyboard in at a time,
            # and run this:
            #
            #   >>> from serial.tools.list_ports import comports
            #   >>> [p.location for p in comports()]
            #   ['1-1:x.1']
            map = {}
            from serial.tools.list_ports import comports
            for port in comports():
                map.update({
                    mapfile[port.location]['serialnumber']: {
                        'port': port,
                        'mount': mapfile[port.location]['mountpoint'],
                    }
                })
            return map

    else:  # default behaviour; attempt the implausible
        def _get_map():
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

    # Cache map & return result
    global _cached_map
    if refresh or (_cached_map is None):
        _cached_map = _get_map()
    return _cached_map
