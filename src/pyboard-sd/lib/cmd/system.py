import sys
import pyb
import machine
import time

from sched import loop

from .mapping import instruction


# ------- machine_reset
@instruction
def machine_reset(send, t=50):
    """
    Resets the pyboard

    :param t: time until reset (unit: ms) (default: 50ms)
    :type t: :class:`int`
    """
    # Reset after delay (default: 50ms).
    # Alow host to gracefully disconnect serial port before hard reset occurs.
    loop.call_later_ms(t, machine.reset)

@instruction
def bootloader_mode(send, t=50):
    """
    Reets pyboard, and it will boot into bootloader mode

    :param t: time until reset (unit: ms) (default: 50ms)
    :type t: :class:`int`
    """
    # Reset after delay (default: 50ms).
    # Alow host to gracefully disconnect serial port before hard reset occurs.
    loop.call_later_ms(t, pyb.bootloader)


# ------- system info
@instruction
def get_system_info(send):
    send({
        'imp': list(sys.implementation),
        'ver': sys.version,
        'platform': sys.platform,
    })

@instruction
def get_ticks_ms(send):
    """
    Get ticks since boot
    """
    send(time.ticks_ms())
