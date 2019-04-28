Welcome to ``upytester``'s documentation!
===============================================


What is ``upytester``?
----------------------------------

``upytester`` is a cPython library to facilitate running
:class:`unittest.TestCase` tests on a host computer to stimulate and
evaluate hardware via a micro-controller running MicroPython (specifically
a *pyboard*).


Why use ``cPython``:``MicroPython``?
--------------------------------------------

Using a test-bench with ``upytester`` for stimulus and evaluation has
the following advantages:

* Hardware is cheap
* Software is free
* All test code is in Python
* Tests built in an established :mod:`unittest` framework
* Tests can utilise real-time features to stimulate and evaluate with very
  accurate timing
* Custom models can be offloaded to a *pyboard*
* Exceptions raised on a *pyboard* is propagated back to the host (making
  debugging very easy)
* Expandable: if there isn't enough runtime on one *pyboard*, or you're
  running out of IO ports, just plug another *pyboard* in

Many test-bench solutions require proprietary hardware and licensing to use
which can make a project very expensive.

It's also rare to find solutions for custom real-time behaviour that doesn't
create messy test code (if at all).


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   about/index
   examples/index
   circuitry/index
   api/host/modules
   api/pyboard/modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
