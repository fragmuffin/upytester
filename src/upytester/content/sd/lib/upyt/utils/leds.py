import pyb
import uasyncio as asyncio

class _LedOnContext(object):
    def __init__(self, led_index):
        self.led = pyb.LED(led_index)

    def __enter__(self):
        self.led.on()

    def __exit__(self, *args):
        self.led.off()


def led_on(*args, **kwargs):
    """
    Keeps a LED on while in context.

    For example, the following code will turn the red LED on for 100ms::

        >>> from time import sleep
        >>> from utils import led_on
        >>> with led_on(1):
        ...     sleep(0.1)
    """
    return _LedOnContext(*args, **kwargs)


async def startup_sequence():
    """Flash onboard LEDs in sequence indicating successful start."""
    leds = [pyb.LED(i+1) for i in range(4)]
    for i in [3, 2, 1, 0, 1, 2, 3]:
        leds[i].on()
        await asyncio.sleep_ms(50)
        leds[i].off()
