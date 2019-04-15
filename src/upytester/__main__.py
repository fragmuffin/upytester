#!/usr/bin/env python

import sys
import os
import time
import argparse
import functools
from fnmatch import fnmatch
import inspect

import upytester


_this_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# Defaults
DEFAULT_SOURCE = os.path.join(_this_path, 'content')


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

def t_serial_number(pattern):
    serial_numbers = [
        s for s in upytester.PyBoard.connected_serial_numbers()
        if fnmatch(s, pattern)
    ]
    if len(serial_numbers) != 1:
        raise argparse.ArgumentTypeError(
            "could not find serial matching pattern: {!r}".format(pattern)
        )
    return serial_numbers[0]

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
    'serialnum', default=None, type=t_serial_number, metavar="SERIAL", nargs="?",
    help="PyBoard's serial number (run with --list to list all connected devices)",
)
parser.add_argument(
    '--source', default=None, type=str,
    help="If the action is to SYNC, the contents of this folder is "
         "synchronised to the pyboard's SD card (instead of the default)",
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


# Default Serial Number
#   If no serial is given, and only 1 pyboard is connected, default to that
if (args.serialnum is None) and (args.action not in ('list',)):
    serial_numbers = serial_numbers = upytester.PyBoard.connected_serial_numbers()
    if len(serial_numbers) <= 0:
        raise ValueError("no connected pyboards found")
    elif len(serial_numbers) > 1:
        raise ValueError("multiple pyboards found, specify one by SERIAL")
    else:
        args.serialnum = serial_numbers[0]

# ====================== Retry Loop Utility ======================
from contextlib import contextmanager
from upytester.pyboard.utils.exceptions import PyBoardNotFoundError, DeviceFileNotFoundError

RETRY_DURATION = 30  # (unit: seconds)
RETRY_PERIOD = 1  # (unit: seconds)

def _log(text, flush=False):
    if not args.quiet:
        sys.stdout.write(text)
        if flush:
            sys.stdout.flush()

def _retry_loop(title=None):
    if title:
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

def retry(title=None):
    """
    Function will be repeatedly called until it succeeds.
    """
    def retry_decorator(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            for context in _retry_loop(title):
                with context:
                    func(*args, **kwargs)
                    break
        return inner
    return retry_decorator

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
    @retry("Mounting " + medium)
    def mount():
        pyboard = upytester.PyBoard(args.serialnum, auto_open=False)
        getattr(pyboard, 'mount_' + medium)()
    mount()


def action_unmount():
    medium = 'flash' if args.flash else 'sd'
    @retry("Unmounting " + medium)
    def unmount():
        pyboard = upytester.PyBoard(args.serialnum, auto_open=False)
        getattr(pyboard, 'unmount_' + medium)()
    unmount()


def action_comport():
    pyboard = upytester.PyBoard(args.serialnum, auto_open=False)
    _log("{}\n".format(pyboard.comport.port))


def action_sync():
    # Create instance
    @retry("Object")
    def create_instance():
        global pyboard
        pyboard = upytester.PyBoard(args.serialnum, auto_open=False)
        _log('{!r}'.format(pyboard))
    create_instance()

    # Mount filesystem
    medium = 'flash' if args.flash else 'sd'
    @retry("Mounting " + medium)
    def mount_filesystem():
        global pyboard
        getattr(pyboard, 'mount_' + medium)()
    mount_filesystem()

    # --- Sync Files
    prj_data = upytester.project.get_bench_config()
    # Main source (for given medium)
    prj_src = args.source
    if not prj_src:
        prj_src = prj_data.get('bench', {}).get('source', {}).get(medium, os.path.join(DEFAULT_SOURCE, medium))
    # Bench lib
    prj_lib = prj_data.get('bench', {}).get('libraries', {}).get(medium, None)

    # Main
    @retry("Sync Main")
    def sync_main():
        global pyboard
        getattr(pyboard, 'sync_to_' + medium)(
            prj_src,
            force=args.force,
            dryrun=args.dryrun,
            quiet=args.quiet,
            exclude=os.path.join('lib_bench', '*') if prj_lib else None,
        )
    sync_main()

    # Sync Project Files
    @retry("Sync Project")
    def sync_prj(prj_lib):
        global pyboard
        getattr(pyboard, 'sync_to_' + medium)(
            prj_lib,
            force=args.force,
            dryrun=args.dryrun,
            quiet=args.quiet,
            subdir='lib_bench',
        )

    if prj_lib:
        sync_prj(prj_lib)

    # --- Unmount filesystem
    @retry("Unmounting")
    def unmount_filesystem():
        global pyboard
        getattr(pyboard, 'unmount_' + medium)()
    unmount_filesystem()

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
