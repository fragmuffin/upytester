import pyb
import machine
import micropython

import time
import json

import uasyncio as asyncio

from utils import external_interrupt
from cmd import interpret, get_sender
import components

# Allocate memory for callback debugging
micropython.alloc_emergency_exception_buf(100)

def _startup_flash():
    # Flash onboard LEDs in sequence
    for i in [4, 3, 2, 1, 2, 3, 4]:
        pyb.LED(i).on()
        time.sleep(0.05)
        pyb.LED(i).off()

_flashy_startup()

vcp = pyb.USB_VCP()

# Interrupt on 'USR' button press. stop mainloop
keepalive = True

@external_interrupt('SW', machine.Pin.PULL_UP, pyb.ExtInt.IRQ_FALLING)
def stop_mainloop(interrupt):
    global keepalive
    keepalive = False


_sender_func = get_sender(vcp)

def process_line(line):
    # Receive & Respond
    obj = json.loads(line)
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
    while keepalive:
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
from sched import loop  # asyncio.get_event_loop()
loop.run_until_complete(listener())

# after mainloop, flash LED, close serial over USB.
#   (end of mainloop will open a repl for debugging)
pyb.LED(2).on()
time.sleep(0.05)
pyb.LED(2).off()
