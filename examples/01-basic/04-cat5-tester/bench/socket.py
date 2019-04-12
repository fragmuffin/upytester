
from collections import namedtuple

SocketPin = namedtuple('SocketPin', (
    'device',  # upytester.PyBoard instance
    'pin',  # name of pin: (eg: 'X1')
))

class RJ45Socket(object):
    """
    An RJ45 socket simply has 8 pins, numbered 1 through 8.
    """
    def __init__(self, pins, mode):
        """
        :param pins: list of pins to stimulate / evaluate
        :type pins: :class:`List` of :class:`SocketPin`
        :param mode: ```'stim'``` or ```'eval'```
        :type mode: :class:`str`
        """
        self._pins = pins
        self._mode = mode

        self.initialise()

    def initialise(self):
        """
        Send configuration to configured pyboard(s)
        """
        pin_mode = 'out' if self._mode == 'stim' else 'in'
        for pin in self._pins:
            pin.device.config_pin(pin.pin, mode=pin_mode, pull='down')

    @property
    def pin_count(self):
        return len(self._pins)

    def pin_value(self, index, value=None):
        """
        Get / Set pin value (high or low)

        :param index: pin index (mapped as ```pins``` in constructor)
        :type index: :class:`int`
        :param value: if set, output value is set to given value
        :type value: :class:`bool`
        """
        pin = self._pins[index]

        if value is None:
            receiver = pin.device.get_pin(pin.pin)
            return receiver()['v']
        else:
            pin.device.set_pin(
                pin.pin,
                1 if value else 0
            )
