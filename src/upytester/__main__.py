#!/usr/bin/env python

import sys
import time
import argparse

import upytester

# ====================== Argument Parsing ======================
# Artument Types
ALLOWED_ACTIONS = (
    'list',
    'mount',
    'unmount',
    'comport',
    'sync',
    'reset',
    'break',
)

def t_action(value):
    value = value.lower()
    if value not in ALLOWED_ACTIONS:
        raise argparse.ArgumentTypeError(
            "action {!r} not recognized".format(value)
        )
    return value

# Parser
parser = argparse.ArgumentParser(
    description="Control and query how a PyBoard is connected",
)

parser.add_argument(
    'action', default=None, type=t_action, metavar="ACTION", nargs=1,
    help="What action to perform, options are: {{{}}}".format(
        "|".join(ALLOWED_ACTIONS),
    ),
)
parser.add_argument(
    'serialnum', default=None, type=str, metavar="SERIAL", nargs="?",
    help="PyBoard's serial number (run with --list to list all connected devices)",
)
parser.add_argument(
    'folder', default=None, type=str, metavar="FOLDER", nargs="?",
    help="If the action is to SYNC, the contents of this folder is "
         "synchronised to the pyboard's SD card",
)

parser.add_argument(
    '--force', default=False, action='store_true',
    help="if the action is to SYNC, marker file(s) presence in the "
         "destination folder is ignored.",
)
parser.add_argument(
    '--dryrun', default=False, action='store_true',
    help="if the action is to SYNC, the source & destination folders are "
         "printed to stdout, but no action is taken",
)
parser.add_argument(
    '--quiet', default=False, action='store_true',
    help="if set, output to STDOUT will be minimal",
)
parser.add_argument(
    '--flash', default=False, action='store_true',
    help="If set, actions such as {mount|unmount|sync} are performed on flash, "
         "the default is sd",
)

# Evaluate
args = parser.parse_args()


# ====================== Retry Loop Utility ======================
from contextlib import contextmanager
from fnmatch import fnmatch
from upytester.pyboard.utils.exceptions import PyBoardNotFoundError, DeviceFileNotFoundError

RETRY_DURATION = 30  # (unit: seconds)
RETRY_PERIOD = 1  # (unit: seconds)

def _log(text, flush=False):
    if not args.quiet:
        sys.stdout.write(text)
        if flush:
            sys.stdout.flush()

def retry_loop(title):
    """
    Repeatedly runs code until it doesn't raise an exception.
    Run each second, for maximum of 30 seconds.

    Usage::

        for context in retry_loop():
            with context:
                perform_task()
                break
    """
    _log(title + ': ')

    @contextmanager
    def try_except(surpress=False):
        try:
            yield
            _log('\n', flush=True)
        except (PyBoardNotFoundError, DeviceFileNotFoundError):
            if surpress:
                _log('.', flush=True)
            else:
                _log('\n', flush=True)
                raise

    i = int(RETRY_DURATION / RETRY_PERIOD)
    while True:
        i -= 1
        yield try_except(i > 0)
        time.sleep(RETRY_PERIOD)


# ====================== Actions ======================
def action_list():
    _log("Connected PyBoards: <serial> <comport> <mountpoint>\n")

    # Gets list of serial numbers
    serial_numbers = upytester.PyBoard.connected_serial_numbers()
    if not serial_numbers:
        _log("    (none found)\n")
        return 0

    # Print info about each one
    for serial_number in sorted(serial_numbers):
        pyboard = upytester.PyBoard(serial_number, auto_open=False)
        _log("    {serial:<15s} {device:<15s} {mount}\n".format(
            serial=pyboard.serial_number,
            device=pyboard.comport.port,
            mount=pyboard.mountpoint_sd,
        ))


def action_mount():
    medium = 'flash' if args.flash else 'sd'
    for context in retry_loop("Mounting " + medium):
        with context:
            pyboard = upytester.PyBoard(args.serialnum, auto_open=False)
            getattr(pyboard, 'mount_' + medium)()
            break


def action_unmount():
    medium = 'flash' if args.flash else 'sd'
    for context in retry_loop("Unmounting " + medium):
        with context:
            pyboard = upytester.PyBoard(args.serialnum, auto_open=False)
            getattr(pyboard, 'unmount_' + medium)()
            break


def action_comport():
    pyboard = upytester.PyBoard(args.serialnum, auto_open=False)
    _log("{}\n".format(pyboard.comport.port))


def action_sync():
    # Find serial number
    for context in retry_loop("Serial"):
        with context:
            serial_numbers = [
                s for s in upytester.PyBoard.connected_serial_numbers()
                if fnmatch(s, args.serialnum)
            ]
            if len(serial_numbers) != 1:
                raise PyBoardNotFoundError(
                    "could not find serial: {!r}".format(args.serialnum)
                )
            serial_num = serial_numbers[0]
            _log('{}'.format(serial_num))
            break

    # Create instance
    for context in retry_loop("Object"):
        with context:
            pyboard = upytester.PyBoard(serial_num, auto_open=False)
            _log('{!r}'.format(pyboard))
            break

    # Mount filesystem
    medium = 'flash' if args.flash else 'sd'
    for context in retry_loop("Mounting " + medium):
        with context:
            getattr(pyboard, 'mount_' + medium)()
            break

    # Sync Files
    for context in retry_loop("Sync"):
        with context:
            getattr(pyboard, 'sync_to_' + medium)(
                args.folder,
                force=args.force,
                dryrun=args.dryrun,
                quiet=args.quiet,
            )
            break

    # Unmount filesystem
    for context in retry_loop("Unmounting " + medium):
        with context:
            getattr(pyboard, 'unmount_' + medium)()
            break

    return 0


def action_reset():
    pyboard = upytester.PyBoard(args.serialnum)
    pyboard.machine_reset(t=500)
    pyboard.close()


def action_break():
    pyboard = upytester.PyBoard(args.serialnum)
    pyboard.break_loop()
    pyboard.close()


# ====================== Mainline ======================
errorcode = 0
if args.action:
    # Execute whatever action was requested
    errorcode = globals()['action_{}'.format(args.action[0])]()

exit(errorcode)
