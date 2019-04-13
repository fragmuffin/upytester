Examples
==============

Example tests are stored in the
`examples folder <https://github.com/fragmuffin/upytester/tree/master/examples>`_.

The following pages in this documentation walk through each example, and how
they're different from the last.

It's recommended you have a rough understanding of the :mod:`unittest` framework
and how to use it.

.. toctree::
   :maxdepth: 2
   :caption: Example Index:

   01-basic/index
   02-on-board-components/index
   03-sample-project/index

Running Tests
--------------------

Each of the test folders contains a ``.upytester-config.yml`` file. This file
maps a pyboard's serial number to a name used to setup the bench.

For example::

   devices:
       pyb_a:
           serial: '0123456789AB'

``pyb_a`` is the human readable name for the pyboard on the test bench,
and ``0123456789AB`` is its serial number.

Find your pyboard's serial number by connecting it, and running::

   $ upytester list
   Connected PyBoards: <serial> <comport> <mountpoint>
       3976346C3436    /dev/ttyACM0    None

Change the serial number in the ``.upytester-config.yml`` file to your
pyboard's serial number.

Then run the test with::

   $ python -m unittest discover -v
