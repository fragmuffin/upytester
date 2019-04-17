import machine
import pyb


def external_interrupt(pin_id, pull, transition):
    """
    Triggers the decorated function from an external interrupt.

    Example::

        keepalive = True

        @external_interrupt('SW', machine.Pin.PULL_UP, pyb.ExtInt.IRQ_FALLING)
        def do_stuff(interrupt):
            global keepalive
            keepalive = False

        while keepalive:
            do_stuff()
            time.sleep(0.01)

    """
    def inner(func):
        # Setup external pin
        pin = machine.Pin(pin_id, machine.Pin.IN, pull)
        ext_int = pyb.ExtInt(pin, transition, pull, func)
        return func

    return inner
