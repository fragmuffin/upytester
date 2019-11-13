import pyb

import upyt.sched
from .mapping import remote


@remote
class LED(pyb.LED):
    """Remotely accessible LED."""

    def blink(self, duration: int = 1, intensity: int = 0xff):
        """
        Turn LED on for the duration at the given intensity.

        note: process is non-blocking

        :param duration: time to keep the LED on (unit: ms)
        :param intensity: intensity of LED (if supported) (range: ``0-255``)
        """
        # Turn LED on
        self.intensity(max(0, min(intensity, 0xff)))
        # Turn LED off (after a delay)
        upyt.sched.loop.call_later_ms(duration, self.off)
