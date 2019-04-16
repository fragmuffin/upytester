.. _examples.components.led_blink:

LED Blink
======================

In this example we'll create a custom instruction on the pyboard to perform
a specific task.

We'll be re-creating the :meth:`blink_led` with a blinking behaviour
instead of just turning on for a set duration.

Bench Setup
------------------

The only physical requirement for this test is a pyboard connected via USB.


On Board Library
------------------

The point of on-board components is that they're executing directly on the
pyboard. This code is stored in a folder nested in the project, defined
in the ``.upytester-bench.yml`` file:

.. literalinclude:: src/01-led-blink/.upytester-bench.yml

This library is synchronised onto the pyboard with::

   upytester sync

If the ``upytester sync`` command finds the bench configuration file, it will
mirror that directories contents onto the ``lib_bench`` folder on the SD card.

For this example, we've added an :meth:`@instruction <instruction>`
called ``custom_blinker``:

.. literalinclude:: src/01-led-blink/benchlib-sd/customled.py

Note that there is also a ``bench.py`` file. This is always imported just
prior to the main scheduler loop starts (if it exists).

.. literalinclude:: src/01-led-blink/benchlib-sd/bench.py

Importing the ``customled`` module ensures the :meth:`@instruction <instruction>`
decorator registers the method(s) it decorates as methods callable by the host.


Test Case
-----------------

The test itself simply calls the :meth:`@instruction <instruction>` registered
method from the host pc.

.. literalinclude:: src/01-led-blink/test_led.py
  :pyobject: LEDTest

If all of this has worked, you should see the yellow LED blink a few times.
The test will actually complete before the blinking stops, because it's
running asynchronously on the board.
