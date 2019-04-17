import pyb

from .mapping import instruction, send


@instruction
def ping(value=0):
    return {'r': 'ping', 'value': value + 1}


@instruction
def get_switch():
    switch_obj = pyb.Switch()
    return {'value': switch_obj.value()}
