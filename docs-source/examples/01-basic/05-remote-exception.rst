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
   :pyobject: ExceptionTest.test_bad_ping_sync

The given ``value`` is returned with ``1`` added to it.
So when the ping response is created on the pyboard, it will attempt to
run ``'abc' + 1`` which will raise an exception.

That exception will be transmitted back to the host, and ultimately fail
the test.


Test Execution
-------------------

Synchronous (default)
^^^^^^^^^^^^^^^^^^^^^^^^^^

Execute the specific testcase with::

   python -m unittest test_exception.ExceptionTest.test_bad_ping_sync

The output::

   E
   ======================================================================
   ERROR: test_bad_ping_sync (test_exception.ExceptionTest)
   ----------------------------------------------------------------------
   Traceback (most recent call last):
     File "/home/nymphii/prj/upytester/examples/01-basic/05-remote-exception/test_exception.py", line 15, in test_bad_ping_sync
       receiver = self.pyb_a.ping(value='abc')
     File "/home/nymphii/.virtualenvs/upytester/lib/python3.5/site-packages/upytester/pyboard/pyboard.py", line 511, in instructon
       return self.send(payload)
     File "/home/nymphii/.virtualenvs/upytester/lib/python3.5/site-packages/upytester/pyboard/pyboard.py", line 403, in send
       raise response
   upytester.pyboard.exceptions.PyBoardError: <PyBoard[3976346C3436]: pyb_a>
     Traceback (most recent call last):
       File "main.py", line 99, in <module>
       File "main.py", line 99, in <module>
       File "main.py", line 95, in <module>
       File "/sd/lib/uasyncio/core.py", line 180, in run_until_complete
       File "/sd/lib/uasyncio/core.py", line 154, in run_forever
       File "/sd/lib/uasyncio/core.py", line 109, in run_forever
       File "/sd/lib/uasyncio/core.py", line 177, in _run_and_stop
       File "main.py", line 73, in listener
       File "main.py", line 57, in process_line
       File "/sd/lib/upyt/cmd/mapping.py", line 102, in interpret
       File "/sd/lib/upyt/cmd/test.py", line 8, in ping
     TypeError: can't convert 'int' object to str implicitly

   ----------------------------------------------------------------------
   Ran 1 test in 0.292s

   FAILED (errors=1)


Bad Practice
-------------------

To reiterate the above *note* on what *not* to do::

   def test_bad_practice(self):
       # NEVER do this!!
       with self.assertRaises(PyBoardError):
           self.pyb_a.ping(value='abc')

The test will pass, and mask the reason for failure of the next test.
