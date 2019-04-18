.. _examples.basic.remote-exception:

Remote Exception
========================

For this example we'll send an invalid request to the pyboard, causing it
to raise an exception.

That exception will then effectively propogate back to the host, cause the
test to fail, and give you a clear indication of what went wrong on the
remote.

.. note::

   Exceptions should not be raised (without being caught) on your test-bench
   by design.

   An exception will halt the runtime on the pyboard, effectively rendering
   your test-bench useless for the remaining tests.


Bench Setup
------------------

The only requirement for this test is a pyboard connected via USB.


Test Case
-----------------

We'll call the :meth:`ping() <upyt.cmd.test.ping>` instruction with a bad
``value`` type.

.. literalinclude:: src/05-remote-exception/test_exception.py
   :pyobject: ExceptionTest.test_bad_ping

The given ``value`` is returned with ``1`` added to it.
So when the ping response is created on the pyboard, it will attempt to
run ``'abc' + 1`` which will raise an exception.

That exception will be transmitted back to the host, and ultimately fail
the test.


Test Execution
-------------------

::

   $ python -m unittest discover -v
   test_bad_ping (test_exception.ExceptionTest) ... ERROR

   ======================================================================
   ERROR: test_bad_ping (test_exception.ExceptionTest)
   ----------------------------------------------------------------------
   Traceback (most recent call last):
     File "/home/nymphii/prj/upytester/examples/01-basic/05-remote-exception/test_exception.py", line 16, in test_bad_ping
       response = receiver()
     File "/home/nymphii/.virtualenvs/upytester/lib/python3.5/site-packages/upytester/pyboard/pyboard.py", line 373, in receive
       raise obj
   upytester.pyboard.exceptions.PyBoardError: <PyBoard[3976346C3436]: pyb_a>
     Traceback (most recent call last):
       File "main.py", line 92, in <module>
       File "main.py", line 92, in <module>
       File "main.py", line 88, in <module>
       File "/sd/lib/uasyncio/core.py", line 180, in run_until_complete
       File "/sd/lib/uasyncio/core.py", line 154, in run_forever
       File "/sd/lib/uasyncio/core.py", line 109, in run_forever
       File "/sd/lib/uasyncio/core.py", line 177, in _run_and_stop
       File "main.py", line 66, in listener
       File "main.py", line 50, in process_line
       File "/sd/lib/upyt/cmd/mapping.py", line 102, in interpret
       File "/sd/lib/upyt/cmd/test.py", line 8, in ping
     TypeError: can't convert 'int' object to str implicitly

   ----------------------------------------------------------------------
   Ran 1 test in 0.338s

   FAILED (errors=1)


Bad Practice
-------------------

To reiterate the above *note* on what *not* to do::

   def test_bad_practice(self):
       # NEVER do this!!
       with self.assertRaises(PyBoardError):
           self.pyb_a.ping(value='abc')

The test will pass, and mask the reason for failure of the next test.
