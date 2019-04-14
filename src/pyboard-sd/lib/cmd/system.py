import sys
import pyb
import machine
import time

import sched

from .mapping import instruction, send


# ------- machine_reset
@instruction
def machine_reset(t=50):
    """
    Resets the pyboard

    :param t: time until reset (unit: ms) (default: 50ms)
    :type t: :class:`int`
    """
    # Reset after delay (default: 50ms).
    # Alow host to gracefully disconnect serial port before hard reset occurs.
    sched.loop.call_later_ms(t, machine.reset)

@instruction
def bootloader_mode(t=50):
    """
    Reets pyboard, and it will boot into bootloader mode

    :param t: time until reset (unit: ms) (default: 50ms)
    :type t: :class:`int`
    """
    # Reset after delay (default: 50ms).
    # Alow host to gracefully disconnect serial port before hard reset occurs.
    loop.call_later_ms(t, pyb.bootloader)


@instruction
def break_loop():
    import sched
    sched.keepalive = False

# ------- system info
@instruction
def get_system_info():
    return {
        'imp': list(sys.implementation),
        'ver': sys.version,
        'platform': sys.platform,
    }

@instruction
def get_ticks_ms():
    """
    Get ticks since boot
    """
    return time.ticks_ms()
