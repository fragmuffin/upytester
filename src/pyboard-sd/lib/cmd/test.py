import pyb
import time

from .mapping import instruction


# ------- blink
@instruction
def blink(send, led=4, intensity=0xff, duration=0.001):
    led_obj = pyb.LED(led)
    led_obj.intensity(intensity)
    time.sleep(duration)
    led_obj.intensity(0)


# ------- ping
@instruction
def ping(send, value=0):
    send({'r': 'ping', 'value': value + 1})
