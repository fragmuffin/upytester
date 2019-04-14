Examples
==============

Example tests are stored in the
`examples folder <https://github.com/fragmuffin/upytester/tree/master/examples>`_.

Running Tests
--------------------

Each test looks for a ``.upytester.yml`` file, first in the current working
path, then in your home directory.
This file maps a pyboard's serial number to a name used to setup the bench.

All example tests uses ``pyb_a`` as the name for the pyboard (and for
examples that use more than 1 pyboard, the second is named ``pyb_b``)

Example ``.upytester.yml`` content::

   devices:
       pyb_a:
           serial: '0123456789AB'
       pyb_b:
           serial: 'BA9876543210'

Find your pyboard serial number(s) by connecting them via USB, and running::

   $ upytester list
   Connected PyBoards: <serial> <comport> <mountpoint>
       3976346C3436    /dev/ttyACM0    None
       497612578916    /dev/ttyACM1    None

This must be done for each host used to run the example tests because every
pyboard's serial number is different... that's sort of the point of them.

Then run the test(s) from within the example folder.
For :ref:`examples.basic.ping` you would run::

   $ cd examples/01-basic/01-ping
   $ python -m unittest discover -v
   test_ping (test_ping.PingTest) ... ok

   ----------------------------------------------------------------------
   Ran 1 test in 0.226s

   OK


Example List
--------------------

The following pages in this documentation walk through each example, and how
they're different from the last.

It's recommended you have a rough understanding of the :mod:`unittest` framework
and how to use it.

.. toctree::
   :maxdepth: 2

   01-basic/index
   02-on-board-components/index
   03-sample-project/index
