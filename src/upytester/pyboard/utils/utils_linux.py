import sys
import os
import subprocess
from glob import glob
from serial.tools.list_ports import comports
import re
from collections import defaultdict

# Local Modules
from .exceptions import PyBoardNotFoundError, DeviceFileNotFoundError


# rsync line filtering
DELETE_REGEX = re.compile(r'^deleting ')
FOLDER_REGEX = re.compile(r'/$')


# ========================== COM port & Info ==========================
PORT_INFO_REGEX_MAP = {
    'manufacturer': re.compile(r'micropython', re.IGNORECASE),
    'description': re.compile(r'pyboard', re.IGNORECASE),
}

def connected_serial_numbers():
    """
    Finds all pyboards connected via USB, and returns a list of their
    serial numbers.

    :rtype: :class:`list` of :class:`str`
    """
    serial_numbers = []
    for port_info in comports():
        is_pyboard = all(
            (
                regex.search(getattr(port_info, key))
                if getattr(port_info, key, None)
                else False
            )
            for (key, regex) in PORT_INFO_REGEX_MAP.items()
        )
        if is_pyboard:
            serial_numbers.append(port_info.serial_number)
    return serial_numbers

def find_portinfo(pyboard):
    """
    Finds the comport associated with the given PyBoard.

    :param pyboard: The connected device in question
    :type pyboard: :class:`pyboard.PyBoard`
    :return: information container class for a single serial port, or `None`
    :rtype: :class:`serial.tools.list_ports_common.ListPortInfo`
    """
    # --- All serial ports
    port_info_list = [
        c for c in comports()
        if c.serial_number == pyboard.serial_number
    ]

    if not port_info_list:
        raise PyBoardNotFoundError("pyboard not found: '%s'" % pyboard.serial_number)
    elif len(port_info_list) > 1:
        raise PyBoardNotFoundError("multiple pyboards found: '%s'" % pyboard.serial_number)

    return port_info_list[0]


# ========================== Disks (SD card / Flash) ==========================
class StorageDevice:
    # Override in inheriting class
    DEVICE_FILE_PREFIX = None
    DEVICE_MARKER_FILE = None

    @classmethod
    def find_device_file(cls, pyboard, suffix='-part1'):
        device_list = glob(
            '/dev/disk/by-id/usb-*_{prefix}_{serial}-*{suffix}'.format(
                prefix=cls.DEVICE_FILE_PREFIX,
                serial=pyboard.serial_number,
                suffix=suffix,
            )
        )
        if len(device_list) != 1:
            raise DeviceFileNotFoundError(
                "could not find {cls_name} device file for {device!r}".format(
                    cls_name=cls.__name__,
                    device=pyboard,
                )
            )
        return device_list[0] if (len(device_list) == 1) else None

    @classmethod
    def get_udisksctl_info(cls, pyboard):
        info_dict = defaultdict(lambda: None)

        try:
            # Run
            cmd = ['udisksctl', 'info', '--block-device', cls.find_device_file(pyboard)]
            with subprocess.Popen(cmd, stdout=subprocess.PIPE) as process:
                # Map output to dict
                info_regex = re.compile(r'^\s+(?P<key>\S+):\s+(?P<value>.*)\s*$')
                for line in process.stdout:
                    process.poll()
                    match = info_regex.search(line.decode())
                    if match:
                        info_dict[match.group('key')] = match.group('value')
                process.wait()

        except DeviceFileNotFoundError:
            pass  # fail nicely; return an empty dict

        return info_dict

    @classmethod
    def find_mountpoint(cls, pyboard):
        """
        Find the mountpoint of the given pyboard
        """
        mountpoint = cls.get_udisksctl_info(pyboard)['MountPoints']
        # Return mountpoint if it exists
        if isinstance(mountpoint, str) and os.path.isdir(mountpoint):
            return mountpoint
        return None

    @classmethod
    def mount(cls, pyboard):
        """
        Mount the PyBoard's storage medium, and return the mounted folder
        """
        mountpoint = cls.find_mountpoint(pyboard)
        if not mountpoint:
            # Mount SD Card
            proc = subprocess.Popen(
                ['udisksctl', 'mount', '--block-device', cls.find_device_file(pyboard)],
                stdout=subprocess.PIPE,
            )
            proc.communicate()
            mountpoint = cls.find_mountpoint(pyboard)

        return mountpoint

    @classmethod
    def unmount(cls, pyboard):
        """
        Unmount SD card (if mounted)
        """
        if cls.find_mountpoint(pyboard):
            proc = subprocess.Popen(
                ['udisksctl', 'unmount', '--block-device', cls.find_device_file(pyboard)],
                stdout=subprocess.PIPE,
            )
            proc.communicate()

    @classmethod
    def sync_files_to_device(cls, source_path, pyboard, subdir='.', force=False, dryrun=False, quiet=False, exclude=[]):
        """
        Synchronise a filesystem to the pyboard's storage.
        Used to deploy code onto a test bench

        :param source_path: Source folder to sync with SD card
        :type source_path: :class:`str`
        :param pyboard: PyBoard to sync to
        :type pyboard: :class:`upytester.PyBoard`
        :param subdir: Subdirectory on pyboard to sync to
        :type subdir: :class:`str`
        :param force: If `True`, assertion of the pre-existence of placeholder
                      files will be ignored.
        :type force: :class:`bool`
        :param dryrun: If `True`, sync will not be performed, but everything else
                       will be done. Use to manually confirm folder sync if
                       you're concerned about what it'll do.
        :type dryrun: :class:`bool`
        :param quiet: If `True` process will not print anything to stdout
        :type quiet: :class:`bool`
        :param exclude: List of file patterns of files to ignore during sync operation
        :type exclude: :class:`list` of :class:`str`
        """
        # Validate Request
        if not os.path.isdir(source_path):
            raise ValueError(
                "given source_path '{}' does not exist (or is not a folder)".format(source_path)
            )

        mountpoint = cls.find_mountpoint(pyboard)
        if not mountpoint:
            raise ValueError(
                "pyboard's mountpoint {!r} does not exist (or is not a folder)".format(mountpoint)
            )

        # Check for marker files
        check_file_list = [
            #'main.py',
            cls.DEVICE_MARKER_FILE,
        ]
        file_check_passed = all(
            os.path.exists(os.path.join(mountpoint, f))
            for f in check_file_list
        )
        if (not file_check_passed) and (not force):
            raise ValueError(
                (
                    "mountpoint {mountpoint!r} and/or source {source!r} "
                    "does not contain {files} file(s), are you sure you "
                    "want to overwrite everything on that drive? manually create "
                    "files with these names to the SD card if you wish to continue."
                ).format(
                    mountpoint=mountpoint,
                    source=source_path,
                    files=', '.join(check_file_list)
                )
            )

        # Create & Run sync process
        abs_source = os.path.abspath(source_path) + '/'
        abs_dest = os.path.abspath(os.path.join(mountpoint, subdir)) + '/'

        assert os.path.relpath(abs_dest, '/') != '.', "destination is ROOT!!?"

        if not quiet:
            print("Synchronising files:")
            print("    - source: {!r}".format(abs_source))
            print("    - dest:   {!r}".format(abs_dest))

        if not dryrun:
            # Create command list
            #   rsync Options
            #       --archive == -rlnnptgoD (but we need -L)
            #           -r  recurse into directories
            #           -L  transform symlink into referent file/dir
            #           -p  preserve permissions
            #           -t  preserve modification times
            #           -g  preserve group
            #           -o  preserve owner (super-user only)
            #           -D  preserve devices & special files
            #
            #       -h  output numbers in a human-readable format
            #       -c  skip based on checksum, not mod-time & size
            #       -v  verbose
            cmd = ['rsync', '-rLptgoDhcv', '--delete']
            for pattern in exclude:
                cmd += ['--exclude', pattern]
            cmd += [abs_source, abs_dest]

            # Start process
            process = subprocess.Popen(
                cmd,
                #shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Allow process to run
            if not quiet:
                for line in process.stdout:
                    process.poll()
                    l = line.decode().rstrip('\n')
                    # print all lines that are NOT simply listing "some/folder/"
                    if not(FOLDER_REGEX.search(l) and not DELETE_REGEX.search(l)):
                        print(l)
            process.wait()


# --- SD Card
class SDCard(StorageDevice):
    DEVICE_FILE_PREFIX = 'SD_card'
    DEVICE_MARKER_FILE = '.pyboard-sd'


def find_mountpoint_sd(*args, **kwargs):
    return SDCard.find_mountpoint(*args, **kwargs)

def mount_sd(*args, **kwargs):
    return SDCard.mount(*args, **kwargs)

def unmount_sd(*args, **kwargs):
    return SDCard.unmount(*args, **kwargs)

def sync_files_to_sd(*args, **kwargs):
    return SDCard.sync_files_to_device(*args, **kwargs)


# --- Flash
class Flash(StorageDevice):
    DEVICE_FILE_PREFIX = 'Flash'
    DEVICE_MARKER_FILE = '.pyboard-flash'


def find_mountpoint_flash(*args, **kwargs):
    return Flash.find_mountpoint(*args, **kwargs)

def mount_flash(*args, **kwargs):
    return Flash.mount(*args, **kwargs)

def unmount_flash(*args, **kwargs):
    return Flash.unmount(*args, **kwargs)

def sync_files_to_flash(*args, **kwargs):
    return Flash.sync_files_to_device(*args, **kwargs)
