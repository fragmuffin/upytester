Example Test Cases
==========================

Example tests are stored in the
`examples folder <https://github.com/fragmuffin/upytester/tree/master/examples>`_.

Each of the folders in the example directory contains multiple example "projects"
made in an attempt to showcase the original intent of this library, and how
to use it.

As a rule of thumb, all folders in this hierarchy that being with 2 numbers
(like ``01-ping``) contains a sample project; a collection of files that
can be moved to another location and still work the same way.

My advice for beginners would be to copy one of those folders and paste it into
your project as a starting point.


Running Tests
--------------------

Configure
^^^^^^^^^^^^^^

Each test searches for a ``.upytester.yml`` file, in the order:

#. ``.`` - current working
#. ``~`` - user's home directory

This file maps a pyboard's serial number to a name used to setup the bench.
You'll need to create this file.

All example tests uses ``pyb_a`` as the name for the pyboard. For
examples that use more than 1 pyboard, the second is named ``pyb_b`` (optional).

Example ``~/.upytester.yml`` content::

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


Synchronise Files on pyboard
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``upytester`` library runs with the assumption that the referenced
pyboards will be running the ``upytester`` software.

This can simply be done with the ``sync`` action of the ``upytester`` command::

   $ upytester sync 3976346C3436

Note: if you're working with a fresh pyboard, you'll want to run this command
with the ``--force`` flag.

.. note::

   Consider running with ``--force --dryrun`` first to confirm the dest folder
   is on the pyboard.

   All files on the dest folder will be deleted and replaced with the ``upytester``
   codebase. I don't want you to accidentally start deleting family photos.


Execute Tests
^^^^^^^^^^^^^^^^^^^

Now you should be ready to go!

Run the test(s) from an example folder.
For :ref:`examples.basic.ping` you would run::

   $ cd examples/01-basic/01-ping
   $ python -m unittest discover -v
   test_ping (test_ping.PingTest) ... ok

   ----------------------------------------------------------------------
   Ran 1 test in 0.226s

   OK


Example List
----------------------

The following pages in this documentation walk through each example, and how
they're different from the last.

It's recommended you have a rough understanding of the :mod:`unittest` framework
and how to use it.

.. toctree::
   :maxdepth: 2

   01-basic/index
   02-on-board-components/index
   03-sample-project/index
