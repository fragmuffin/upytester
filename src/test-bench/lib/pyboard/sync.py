import sys
import os
import subprocess

from .map import get_pyboard_map


def sync_path_to_sd(source_path, serial_number):
    # Validate Request
    if not os.path.isdir(source_path):
        raise ValueError(
            "given source_path '{}' does not exist (or is not a folder)".format(source_path)
        )

    pyboard_map = get_pyboard_map()
    if serial_number not in pyboard_map:
        raise ValueError(
            "pyboard with serial '{}' could not be found".format(serial_number)
        )

    mountpoint = pyboard_map[serial_number]['mount']
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

    # Sync: source_path -> mountpoint
    if sys.platform.startswith('win'):
        # Windows: Robocopy.exe
        cmd = [
            'Robocopy.exe',
            os.path.abspath(source_path),
            os.path.abspath(mountpoint),
            '/MIR', '/Z', '/W:5',
        ]

    else:
        # Linux: rsync
        cmd = [
            'rsync',
            '-aIvzh', '--delete',
            "{}/".format(os.path.abspath(source_path)),
            "{}/".format(os.path.abspath(mountpoint)),
        ]

    # Create & Run process
    process = subprocess.Popen(
        cmd, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for line in process.stdout:
        process.poll()
        print(line.decode().rstrip('\n'))
    process.wait()
