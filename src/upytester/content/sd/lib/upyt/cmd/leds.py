import pyb

import upyt.sched
from .mapping import instruction, send


@instruction
def blink_led(led=1, intensity=0xff, duration=1):
    """
    Turn LED on for a set duration

    :param led: index of LED 1=red, 2=green, 3=yellow, and 4=blue
    :type led: :class:`int`
    :param intensity: brightness of LED (0-0xff)
    :type intensity: :class:`int`
    :param duration: time to leave LED on
    :type duration: :class:`int`
    """
    led_obj = pyb.LED(led)
    # Turn LED on
    led_obj.intensity(intensity)
    # Turn LED off (after a delay)
    upyt.sched.loop.call_later_ms(duration, lambda: led_obj.intensity(0))


@instruction
def set_led(led=1, intensity=0xff):
    """
    Turn LED on for a set duration

    :param led: index of LED 1=red, 2=green, 3=yellow, and 4=blue
    :type led: :class:`int`
    :param intensity: brightness of LED (0-0xff)
    :type intensity: :class:`int`
    """
    led_obj = pyb.LED(led)
    led_obj.intensity(intensity)
