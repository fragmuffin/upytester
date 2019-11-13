import machine
import pyb

from .mapping import instruction
from .mapping import remote


@remote
class Pin(pyb.Pin):
    """Remote pin control."""

    def __init__(self, id, mode, pull=None, value=None):
        """
        Pin Constructor.

        :param id: name of pin (eg: ``SW``, ``X7``)
        :type id: :class:`str`
        :param mode: pin mode (see table below)
        :type mode: :class:`str`
        :param pull: pull up/down resistor (if any), (see table below)
        :type pull: :class:`str`
        :param value: if pin is an output, initial value can be set
        :type value: :class:`int`

        **Parameter:** ``mode``

        ==============  ======================================
        ``mode`` Value  Pin Behaviour
        ==============  ======================================
        ``'in'``        input
        ``'out'``       (synonymn for 'out_pp')
        ``'out_pp'``    output, with push-pull control
        ``'out_od'``    output, with open-drain control
        ``'af_pp'``     alternate function, pull-pull
        ``'af_od'``     alternate function, open-drain
        ``'analog'``    analog
        ==============  ======================================

        **Parameter:** ``pull``

        ==============  =========================
        ``pull`` Value  Pin Behaviour
        ==============  =========================
        ``None``        no pull up/down
        ``'none'``      no pull up/down
        ``'up'``        pull up resistor
        ``'down'``      pull down resistor
        ==============  =========================
        """
        super().__init__(id)
        self.init(**{
            'mode': {
                'in': pyb.Pin.IN,  # input
                'out': pyb.Pin.OUT,  # (synonymn for 'out_pp')
                'out_pp': pyb.Pin.OUT_PP,  # output, with push-pull control
                'out_od': pyb.Pin.OUT_OD,  # output, with open-drain control
                'af_pp': pyb.Pin.AF_PP,  # alternate function, pull-pull
                'af_od': pyb.Pin.AF_OD,  # alternate function, open-drain
                'analog': pyb.Pin.ANALOG,  # analog
            }[mode],
            'pull': {
                None: pyb.Pin.PULL_NONE,
                'none': pyb.Pin.PULL_NONE,
                'up': pyb.Pin.PULL_UP,
                'down': pyb.Pin.PULL_DOWN,
            }[pull],
        })
        # Set initial value (if given)
        if value is not None:
            self.value(value)
