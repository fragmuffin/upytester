import pyb

# upytester pyboard library
from upyt.cmd import instruction
import upyt.sched

@instruction
def custom_blinker(led=1, iterations=6):
    led = pyb.LED(led)

    def callback():
        led.toggle()
        iterations -= 1
        if iterations > 0:
            upyt.sched.loop.call_later_ms(100, callback)

    upyt.sched.loop.call_soon(callback)
