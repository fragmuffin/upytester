import pyb
import micropython
import uasyncio as asyncio

from .mapping import instruction, send

import upyt.sched

# ------- Maps
can_bus_map = {}
can_tx_msg = {}  # format: {can: {id: (data, period), ... }, ...}


# ------- Configure

@instruction
def config_can(send, bus, mode='normal', extframe=False, prescaler=100, sjw=1, bs1=6, bs2=8, auto_restart=False):
    """
    Configure CAN bus

    :param bus: 1 or 2 (for each CAN controller on the pyboard)
    :type bus: :class:`int`
    """
    _mode = {
        'normal': pyb.CAN.NORMAL,
        'loopback': pyb.CAN.LOOPBACK,
        'silent': pyb.CAN.SILENT,
        'silent_loopback': pyb.CAN.SILENT_LOOPBACK,
    }[mode]

    can = pyb.CAN(
        bus, mode=_mode,
        extframe=extframe,
        prescaler=prescaler, sjw=sjw, bs1=bs1, bs2=bs2,
        auto_restart=auto_restart
    )

    can_bus_map[bus] = can


@instruction
def can_state(send, bus):
    """
    Get the state of a previously configured CAN bus.

    :param bus: 1 or 2 (according to the pyboard's CAN controllers)
    :type bus: :class:`int`

    Response::

        {
            'r': 'can_state',  # in response to can_state request
            'state': x,  # CAN bus state, as string (or None if not configured)
        }
    """
    response = {'r': 'can_state', 'state': None}
    can = can_bus_map.get(bus, None)
    if can is not None:
        response['state'] = {
            pyb.CAN.STOPPED: 'stopped',
            pyb.CAN.ERROR_ACTIVE: 'error_active',
            pyb.CAN.ERROR_WARNING: 'error_warning',
            pyb.CAN.ERROR_PASSIVE: 'error_passive',
            pyb.CAN.BUS_OFF: 'bus_off',
        }.get(can.state(), '???')

    send(response)


# ------- Transmit / Receive : Basic
@instruction
def can_tx(send, bus, id, data, rtr=False):
    can = can_bus_map[bus]
    can.send(bytes(data), id, rtr=rtr)

def _can_tx_p_callback(bus, id):
    # Continually transmit until mapped reference is gone
    #   or an error occurs
    if id in can_tx_msg[bus]:
        (d, p) = can_tx_msg[bus][id]
        can = can_bus_map[bus]
        try:
            can.send(d, id)
        except OSError:  # raised if error during transmission
            # Common reason(s):
            #   - Transmitted frame ACK bit not set
            #       (occurs if all other ECUs are off or passive)
            pass  # do nothing; retry next period
        sched.loop.call_later_ms(p, _can_tx_p_callback, bus, id)

@instruction
def can_tx_p(send, bus, id, data, period):
    """
    Send a CAN message periodically

    :param bus: bus number (1 or 2)
    :type bus: :class:`int`
    :param id: arbitration id of frame
    :type id: :class:`int`
    :param data: list of bytes (integers between 0 and 255)
    :type data: :class:`list`
    :param period: time between transmissions (ms)
    :type period: :class:`int`
    """
    can = can_bus_map[bus]
    if bus not in can_tx_msg:
        can_tx_msg[bus] = {}

    start_async = True
    if id in can_tx_msg[bus]:
        start_async = False  # should already be running,
                             # just change data & period
    can_tx_msg[bus][id] = (bytes(data), period)

    if start_async:
        sched.loop.call_later_ms(0, _can_tx_p_callback, bus, id)

@instruction
def can_tx_p_stop(send, bus, id):
    if bus in can_tx_msg:
        if id in can_tx_msg[bus]:
            del can_tx_msg[bus][id]
            # removal of this key will stop recursion of async function

@instruction
def can_tx_p_stopall(send, bus):
    can_tx_msg[bus] = {}
