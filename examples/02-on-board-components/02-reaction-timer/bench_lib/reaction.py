import pyb
import machine
import time
import micropython

# upytester pyboard library
from upyt.cmd import instruction
from upyt.cmd import send
import upyt.sched


# Callbacks
_start_time = None
_ext_int = None  # interrupt object placeholder
_led = pyb.LED(1)  # LED to illuminate when timing starts

def _respond(end_time):
    global _ext_int
    global _start_time
    _ext_int.disable()
    _led.off()
    send(time.ticks_diff(end_time, _start_time))  # as float

def _cb(interrupt):
    micropython.schedule(_respond, time.ticks_ms())
    #upyt.sched.loop.call_soon(_respond, time.ticks_ms())

@instruction
def reaction_time():
    # Record time called
    global _start_time
    _start_time = time.ticks_ms()
    _led.on()

    # Setup SW input as external interrupt
    global _ext_int
    if _ext_int is None:
        pin = machine.Pin('SW', machine.Pin.IN, machine.Pin.PULL_UP)
        _ext_int = pyb.ExtInt(
            pin, pyb.ExtInt.IRQ_FALLING, machine.Pin.PULL_UP, _cb
        )
    else:
        _ext_int.enable()
