import pyb
import sys
import micropython

import time
import json

import uasyncio as asyncio

# upytester module(s)
from upyt.cmd import interpret
from upyt.cmd.mapping import set_serial_port
from upyt.utils import startup_sequence
import upyt.sched


# Allocate memory for callback debugging
micropython.alloc_emergency_exception_buf(100)

vcp = pyb.USB_VCP()
set_serial_port(vcp)


def process_line(line):
    """Process received line as a upyt command."""
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

    # Interpret command, then respond with 'ok'
    #   Order is imporant:
    #       The host's transmit() method will block until it receives an 'ok'.
    #       With the interpret/response in this order, any exception raised
    #       while interpreting the object will cause the transmit() method
    #       to fail, causing the test itself to fail.
    #   Trade-off:
    #       This makes communication slightly slower, because the command has
    #       to complete before the host can begin to process the next command.
    #       However, it does enable tests to... you know... fail when they
    #       should. So the choice seems like a no-brainer.
    interpret(obj)
    vcp.write(b'ok\r')


async def listener():
    """Read and process lines from Virtual Comm Port (VCP)."""
    # TODO: create a global buffer, and populate via memoryview
    line = b''

    # Stop mainloop on 'USR' button press
    while upyt.sched.keepalive:
        c = vcp.recv(1, timeout=0)  # non-blocking
        if c:
            if c == b'\r':
                process_line(line)
                line = b''
            else:
                line += c
        else:
            await asyncio.sleep_ms(1)

upyt.sched.init_loop()  # initialize asyncio loop object

# Bench Libraries
#   note: imported after scheduler loop initialised, just incase somebody has
#         used "from sched import loop" in a custom lib
sys.path.append('/sd/lib_bench')
sys.path.append('/flash/lib_bench')
try:
    import bench  # noqa: F401
except ImportError as e:
    if "'bench'" not in e.args[0]:
        # import error was not from a nested library fault
        raise
    pass  # else: fail quietly

# Main loop
try:
    upyt.sched.loop.create_task(startup_sequence())
    listener_coroutine = listener()
    upyt.sched.loop.run_until_complete(listener_coroutine)

except KeyboardInterrupt:
    # Blink Green LED
    pyb.LED(2).on()
    time.sleep(0.05)
    pyb.LED(2).off()

except Exception as e:
    # Save Exception for further analysis
    with open('exception.txt', 'w') as fh:
        sys.print_exception(e, fh)
    raise

finally:
    # Cancel listener task
    asyncio.cancel(listener_coroutine)
    # Turn off all LEDs
    for i in range(4):
        pyb.LED(i + 1).off()
