import pyb
import machine
import time
import micropython

# upytester pyboard library
from upyt.cmd import instruction
from upyt.cmd import send
import upyt.sched

@instruction
def reaction_time():
    pin = machine.Pin('SW', machine.Pin.IN, machine.Pin.PULL_UP)
    led = pyb.LED(1)

    # Record time called
    start_time = time.ticks_ms()
    led.on()

    # Define callbacks
    def respond(end_time):
        ext_int.disable()
        led.off()
        send(time.ticks_diff(end_time, start_time))  # as float

    def cb(interrupt):
        micropython.schedule(respond, time.ticks_ms())
        #upyt.sched.loop.call_soon(respond, time.ticks_ms())

    # Setup SW input as external interrupt
    ext_int = pyb.ExtInt(pin, pyb.ExtInt.IRQ_FALLING, machine.Pin.PULL_UP, cb)
