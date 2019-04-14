Switch Evaluation Example
=====================================

The ``test_switch_pressed`` test will pass if the ``USR`` button is being
pressed, and fail otherwise.

This example introduces the use of a container class (``Switch``) for the
pyboard's ``USR`` switch to make test code more readable.


Bench Setup
------------------------

The only requirement for this test is a pyboard connected via USB.

The ``USR`` switch on the pyboard is used for evaluation. The *value* of the
switch is made accessible via the ``Switch`` class:

.. literalinclude:: src/03-switch-evaluation/test_switch.py
   :pyobject: Switch

An instance of ``Switch`` is then created in the ``BenchTest``'s
overridden :meth:`setUpClass() <unittest.TestCase.setUpClass>` method,
referencing the ``pyb_a`` pyboard as the relevant ``device``:

.. literalinclude:: src/03-switch-evaluation/test_switch.py
   :pyobject: BenchTest.setUpClass

Test Case
------------------------

Setting up the ``BenchTest`` like this alows the test-code to be very
short and unambiguous:

.. literalinclude:: src/03-switch-evaluation/test_switch.py
   :pyobject: SwitchTest
