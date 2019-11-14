import sys
import pyb
import machine
import time

import uasyncio as asyncio
import upyt.sched

from .mapping import instruction, send


# ------- machine_reset
@instruction
def machine_reset(t=50):
    """
    Reset the pyboard.

    :param t: time until reset (unit: ms) (default: 50ms)
    :type t: :class:`int`
    """
    # Reset after delay (default: 50ms).
    # Alow host to gracefully disconnect serial port before hard reset occurs.
    upyt.sched.loop.call_later_ms(t, machine.reset)


@instruction
def bootloader_mode(t=50):
    """
    Reets pyboard, and it will boot into bootloader mode.

    :param t: time until reset (unit: ms) (default: 50ms)
    :type t: :class:`int`
    """
    # Reset after delay (default: 50ms).
    # Alow host to gracefully disconnect serial port before hard reset occurs.
    upyt.sched.loop.call_later_ms(t, pyb.bootloader)


@instruction
def break_loop():
    upyt.sched.keepalive = False


# ------- heartbeat
_heartbeat_coroutine = None

HEARTBEAT_PULSE = 20  # duration led is on (unit: ms)
HEARTBEAT_PERIOD = 1000  # time between led flashes (unit: ms)


@instruction
def heartbeat(enabled=True):
    """Show LED indicator that the async loop is running."""
    global _heartbeat_coroutine

    if enabled and (_heartbeat_coroutine is None):
        # Start
        async def heartbeat_task():
            blue_led = pyb.LED(4)  # blue
            while True:
                blue_led.on()
                await asyncio.sleep_ms(HEARTBEAT_PULSE)
                blue_led.off()
                await asyncio.sleep_ms(HEARTBEAT_PERIOD - HEARTBEAT_PULSE)
        _heartbeat_coroutine = heartbeat_task()
        upyt.sched.loop.create_task(_heartbeat_coroutine)

    elif (not enabled) and (_heartbeat_coroutine is not None):
        # Stop
        asyncio.cancel(_heartbeat_coroutine)
        _heartbeat_coroutine = None


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
    """Get ticks since boot."""
    return time.ticks_ms()
