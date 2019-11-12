import pyb

from .mapping import instruction, send


@instruction
def ping(value=0):
    """Return given value + 1, must be an integer."""
    return {'value': value + 1}


@instruction
def get_switch():
    """Onboard switch value."""
    switch_obj = pyb.Switch()
    return {'value': switch_obj.value()}
