Example Circuitry
===============================

The pyboard uses 3.3V for its GPIOs and serial communication lines (such as
:class:`pyb.UART <pyb.pyb.UART>` and :class:`pyb.SPI <pyb.pyb.SPI>`).
:class:`pyb.DAC <pyb.pyb.DAC>` lines also have a maximum voltage of 3.3V.

That may be perfect for some applications, but many "products" being tested
will require 5V logic levels, and other stimulus to trigger certain behaviours,
or simply to prevent fault scenarios.



Examples
---------------

.. toctree::
   :maxdepth: 2

   logic
   analogue

* isolators
* relays & drivers
