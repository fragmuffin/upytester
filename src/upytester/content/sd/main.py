import pyb
import sys
import micropython

import time
import json

import uasyncio as asyncio

# upytester module(s)
from upyt.cmd import listener
from upyt.cmd.mapping import set_serial_port
from upyt.utils import startup_sequence
import upyt.sched


# Allocate memory for callback debugging
micropython.alloc_emergency_exception_buf(100)

# Initialise Serial Interface
vcp = pyb.USB_VCP()
set_serial_port(vcp)

upyt.sched.init_loop()  # initialize asyncio loop object


# Import Bench Libraries
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


try:
    # Start Tasks (including mainloop)
    upyt.sched.loop.create_task(startup_sequence())
    listener_coroutine = listener(vcp)
    upyt.sched.loop.run_until_complete(listener_coroutine)

except KeyboardInterrupt:
    # Blink Green LED
    pyb.LED(2).on()
    time.sleep(0.05)
    pyb.LED(2).off()

except Exception as e:
    # Save Exception for further analysis
    with open('exception.txt', 'w') as fh:
        fh.write(repr(e))
    raise

finally:
    # Cancel listener task
    asyncio.cancel(listener_coroutine)
    
    # Turn off all LEDs
    for i in range(4):
        pyb.LED(i + 1).off()
