import pyb

# upytester pyboard library
from cmd import instruction
import sched

@instruction
def custom_blinker(led=1, iterations=6):
    led = pyb.LED(led)

    def callback():
        led.toggle()
        iterations -= 1
        if iterations > 0:
            sched.loop.call_later_ms(100, callback)

    sched.loop.call_soon(callback)
