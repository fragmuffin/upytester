import pyb


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
