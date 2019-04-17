import machine
import pyb

from .mapping import instruction, send


# ------- Map(s)
pin_map = {}

# ------- Configure

@instruction
def config_pin(id, mode, pull=None, value=None):
    r"""
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
    # Configure pin
    args = {
        'mode': {
            'in': pyb.Pin.IN,  # input
            'out': pyb.Pin.OUT_PP,  # (synonymn for 'out_pp')
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
    }

    pin = pyb.Pin(id, **args)
    if value is not None:
        pin.value(value)

    # Assign pin to map
    pin_map[id] = pin


# ------- Get / Set

@instruction
def get_pin(id):
    pin = pin_map[id]
    return {'pin': id, 'v': pin.value()}


@instruction
def set_pin(id, v):
    pin = pin_map[id]
    pin.value(v)
