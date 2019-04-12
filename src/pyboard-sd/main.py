import pyb
import machine
import micropython

import time
import json

import uasyncio as asyncio

from utils import external_interrupt
from cmd import interpret, get_sender
import sched
try:
    import components
except ImportError:
    pass  # fail quietly


# Allocate memory for callback debugging
micropython.alloc_emergency_exception_buf(100)

def _startup_flash():
    # Flash onboard LEDs in sequence
    for i in [4, 3, 2, 1, 2, 3, 4]:
        pyb.LED(i).on()
        time.sleep(0.05)
        pyb.LED(i).off()

_startup_flash()

vcp = pyb.USB_VCP()

_sender_func = get_sender(vcp)

def process_line(line):
    # Receive & decode data
    try:
        obj = json.loads(line)
    except ValueError:
        # If invalid JSON is received from host, ignore it.
        # why?: I've been receiving "AT" commands from an ubuntu service.
        # ref: https://stackoverflow.com/questions/31774566
        # assumption:
        #   These spurious characters will not be injected in the
        #   middle of a command.
        # TODO: Check what process is using the serial port.
        return

    # Respond
    vcp.write(b'ok\r')

    # Interpret command
    interpret(_sender_func, obj)

async def listener():
    """
    Reads lines from Virtual Comm Port (VCP) and send them to be
    processed.
    """
    # TODO: create a global buffer, and populate via memoryview
    line = b''

    # Stop mainloop on 'USR' button press
    usr_button = pyb.Switch()
    while sched.keepalive:
        c = vcp.recv(1, timeout=0)  # non-blocking
        if c:
            if c == b'\r':
                process_line(line)
                line = b''
            else:
                line += c
        else:
            await asyncio.sleep_ms(1)

# Main loop
sched.init_loop()  # initialize asyncio loop object
try:
    # start asyncio.get_event_loop()
    sched.loop.run_until_complete(listener())
except Exception as e:
    with open('/sd/exception.txt', 'w') as fh:
        fh.write(repr(e))
    raise

# after mainloop, flash LED, close serial over USB.
#   (end of mainloop will open a repl for debugging)
pyb.LED(2).on()
time.sleep(0.05)
pyb.LED(2).off()
