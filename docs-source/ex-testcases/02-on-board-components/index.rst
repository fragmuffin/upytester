.. _examples.components:

On Board Components
==================================

Possibly the most powerful aspect of the ``upytester`` architecture is the
ability to run realtime, and asynchronous code on the pyboard itself.

This enables you to create a test-bench that would otherwise not be possible
with just the host PC, such as:

* Trigger on external interrupts.
* Precice timing with internal timers.
* Cyclic stimulus without messy & repetitive test code.
* (and much more)

These examples showcase what can be done, with some advice on how and
where to start.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   01-led-blink
