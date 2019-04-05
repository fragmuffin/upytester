import sys
import os
import subprocess
from glob import glob
from serial.tools.list_ports import comports

from .exceptions import PyBoardNotFoundError


def find_comport(pyboard):
    """
    Finds the comport associated with the given PyBoard.

    :param pyboard: The connected device in question
    :type pyboard: :class:`pyboard.PyBoard`
    :return: information container class for a single serial port, or `None`
    :rtype: :class:`serial.tools.list_ports_common.ListPortInfo`
    """
    # --- All serial ports
    ports = [c for c in comports() if c.serial_number == pyboard.serial_number]

    if not ports:
        raise PyBoardNotFoundError("pyboard not found: '%s'" % pyboard.serial_number)
    elif len(ports) > 1:
        raise PyBoardNotFoundError("multiple pyboards: '%s'" % pyboard.serial_number)

    return ports[0]


def _find_sd_device_file(pyboard):
    device_list = glob(
        '/dev/disk/by-id/usb-uPy_microSD_SD_card_{}-*-part1'.format(
            pyboard.serial_number
        )
    )
    if len(device_list) != 1:
        raise ValueError("Device file not found")
    return device_list[0]


def _get_udisksctl_info(pyboard):
    # Run
    process = subprocess.Popen(
        ['udisksctl', 'info', '--block-device', _find_sd_device_file(pyboard)],
        stdout=subprocess.PIPE,
    )

    # Map output to dict
    info_dict = defaultdict(lambda: None)
    info_regex = re.compile(r'^\s+(?P<key>\S+):\s+(?P<value>.*)\s*$')
    for line in process.stdout:
        process.poll()
        match = info_regex.search(line)
        if match:
            info_dict[match.group('key')] = match.group('value')
    process.wait()

    return info_dict


def find_mountpoint_sd(pyboard):
    """
    Find the mountpoint of the given pyboard

    :param pyboard: connected device
    :type pyboard: :class:`PyBoard`
    """
    return _get_udisksctl_info(pyboard)['MountPoints']


def mount_sd(pyboard):
    """
    Mount the PyBoard's SD card, and return the mounted folder
    """
    mountpoint = find_mountpoint_sd(pyboard)
    if not mountpoint:
        # Mount SD Card
        proc = subprocess.Popen(
            ['udisksctl', 'mount', '--block-device', _find_sd_device_file(pyboard)],
            stdout=subprocess.PIPE,
        )
        proc.communicate()
        mountpoint = find_mountpoint_sd(pyboard)

    return mountpoint


def unmount_sd(pyboard):
    """
    Unmount SD card (if mounted)
    """
    if find_mountpoint_sd(pyboard):
        proc = subprocess.Popen(
            ['udisksctl', 'unmount', '--block-device', _find_sd_device_file(pyboard)],
            stdout=subprocess.PIPE,
        )
        proc.communicate()


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

    CHECK_FILES = ['main.py', '.pyboard-sdcard']
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
            'rsync',
            '-rLptgoDIvzhi', '--delete',
            "{}/".format(os.path.abspath(source_path)),
            "{}/".format(os.path.abspath(mountpoint)),
        ],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for line in process.stdout:
        process.poll()
        print(line.decode().rstrip('\n'))
    process.wait()
