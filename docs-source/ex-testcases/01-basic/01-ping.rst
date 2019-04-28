.. _examples.basic.ping:


Ping
========================

This is the simplest example of a ``upytester`` test-case. It tests that the
configured pyboard is connected, and responding to serial commands.

This example's implementation is far from the best design for a bench test,
but it is a good starting point to explain how ``upytester`` may be set up
to be useful for your peojct.


Bench Setup
------------------

The only requirement for this test is a pyboard connected via USB.


Test Case
-----------------

Setup
^^^^^^^^^^^^^^

:meth:`TestCase.setUp() <unittest.TestCase.setUp>` is called before each test.
For this test, we use the :meth:`get_device() <upytester.project.get_device>`
method to return a :class:`PyBoard <upytester.PyBoard>` instance to send
commands to, and assign it to ``self.pyb_a``.

.. literalinclude:: src/01-ping/test_ping.py
   :pyobject: PingTest.setUp

Test
^^^^^^^^^^^^^^

The test is done in 3 parts:

.. literalinclude:: src/01-ping/test_ping.py
   :pyobject: PingTest.test_ping

#. ``ping`` is called on the :class:`PyBoard <upytester.PyBoard>` instance.
   This command is serialized and set to to the pyboard via USB.
   It also returns a callable that can be used to receive a response from
   the pyboard.
#. The pyboard's response is stored in ``response``
#. The value of the responce is used to evaluate the test's verdict.

Note: this could have all been done in one line.

::

    self.assertEqual(self.pyb_a.ping(value=100)()['value'], 101)


Tear Down
^^^^^^^^^^^^^^

To compliment :meth:`setUp() <unittest.TestCase.setUp>`,
:meth:`tearDown() <unittest.TestCase.tearDown>` is called *after* each test.

The serial link to the pyboard is closed by calling
:meth:`close() <upytester.PyBoard.close>`

.. literalinclude:: src/01-ping/test_ping.py
   :pyobject: PingTest.tearDown


Improvements
-------------------------

The following improvements can be found in the next example:

* We create and close a new :class:`PyBoard <upytester.PyBoard>`
  instance for each test. This could be done in
  :meth:`TestCase.setUpClass() <unittest.TestCase.setUpClass>` and
  :meth:`TestCase.tearDownClass() <unittest.TestCase.tearDownClass>` instead

* The *bench* deisgn is defined in the test class. Instead this could be
  defined in an inherited class.
