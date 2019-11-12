import pyb

import upyt.sched
from .mapping import remote


@remote
class LED:
    """Remotely accessible LED."""

    def __init__(self, idx):
        """
        Remote for :class:`pyb.LED`.

        :param idx: :class:`int` of range ``{1 <= idx <= 4}``
        """
        self.obj = pyb.LED(idx)

    def on(self):
        """Turn LED on."""
        self.obj.on()

    def off(self):
        """Turn LED off."""
        self.obj.off()

    def intensity(self, val):
        """Set LED intensity."""
        self.obj.intensity(val)

    def blink(self, duration: int = 1, intensity: int = 0xff):
        """
        Turn LED on for the duration at the given intensity.

        note: process is non-blocking

        :param duration: time to keep the LED on (unit: ms)
        :param intensity: intensity of LED (if supported) (range: ``0-255``)
        """
        # Turn LED on
        self.obj.intensity(max(0, min(intensity, 0xff)))
        # Turn LED off (after a delay)
        upyt.sched.loop.call_later_ms(duration, self.obj.off)
