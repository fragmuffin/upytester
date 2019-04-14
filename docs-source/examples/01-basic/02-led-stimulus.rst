LED Stimulus Example
===================================

This test will just turn on some of the pyboard's onboard LEDs, nothing
is actually asserted.

The concept of creating a *bench* ``TestCase`` class is introduced.


Bench Setup
------------------------

The only requirement for this test is a pyboard connected via USB.

The setup of the *bench* is absracted to a ``BenchTest`` class.

.. literalinclude:: src/02-led-stimulus/test_led.py
   :pyobject: BenchTest

The :meth:`setUpClass() <unittest.TestCase.setUpClass>` and
:meth:`tearDownClass() <unittest.TestCase.tearDownClass>` methods
are used to configure the pyboard for all tests in any inheriting class.


Test Case
------------------------

The ``LEDTest`` class inherits from ``BenchTest``, giving each test
contextual access to the configured pyboard as ``self.pyb_a``.

.. literalinclude:: src/02-led-stimulus/test_led.py
   :pyobject: LEDTest

Each test simply turns on a LED for 500ms. No evalution is performed, so both
tests pass as long as no exceptions are raised due to communication problems.
