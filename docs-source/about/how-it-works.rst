.. _about.howitworks:

How ``upytester`` Works
==============================

The ``upytester`` module on a host computer communicates with one or more
pyboards via USB to send them instructions and receive responses.

.. image:: /_static/img/about/arch-hw.svg

Once a instruction is received, a corresponding method is passed the
de-serialised arguments and executed. Any return from that method is
serialised and sent back to the host

.. note::

    The *cPython* module on the host is called ``upytester``.

    The *MicroPython* module on the pyboard is called ``upyt``.


Synchronise pyboard(s)
--------------------------------

The ``upytester`` module operates on the assumption that the pyboard
is running the ``upyt`` application.

.. code-block:: console

    # synchronise files to the pyboard's SD card
    upytester sync 1234567890AB --hardreset

    # if only 1 pyboard is connected, you can simply run...
    upytester sync -R

The term "synchonise" is referring to the filesystem on the microSD card, and
making sure it matches the ``upyt`` application stored on the host.

The ``--hardreset`` argument will force the pyboard to reset, effectively
running the newly synchronised application.


Host ``upytester`` -- pyboard ``upyt``
----------------------------------------

To illustrate in more detail, we'll use :meth:`ping() <upyt.cmd.test.ping>`
as an example.

First we'll create an instance of :class:`PyBoard <upytester.PyBoard>`
on the host to create a connection.

::

    >>> from upytester import PyBoard
    >>> pyboard = PyBoard('1234567890AB')

This will initiate communication to the pyboard to get a list of
instructions it supports.
One of these instructions will be :meth:`ping <upyt.cmd.test.ping>`::

    >>> 'ping' in pyboard.instruction_list
    True
    >>> receiver = pyboard.ping(value=5)

:meth:`ping() <upyt.cmd.test.ping>` is called as an attribute of
``pyboard``, just like a regular method.

All instructions called like this will return a bound reference to
:meth:`PyBoard.receive() <upytester.PyBoard.receive>`
to be used to receive the pyboard's response (if any)::

    >>> response = receiver()

``receiver()`` returns the serialised, then de-serialised object returned by the
method run on the pyboard.
In the case of :meth:`ping() <upyt.cmd.test.ping>`, ``response`` will be::

    # the given value + 1
    >>> response
    {'value': 6}

This pattern of invoking an *instruction* on the pyboard and receiving a
response is done repeatedly, so you might want to get used to the
shorthand version of the above::

    >>> returned_value = pyboard.ping(value=5)()['value']


Instructions
-------------------

An *instruction* is a method defined and executed on the pyboard, and is
directly callable from the host via a :class:`PyBoard <upytester.PyBoard>`
instance.

To continue with :meth:`ping() <upyt.cmd.test.ping>` as an example, this
is how it's implemented on the pyboard::

    from upyt import instruction

    @instruction
    def ping(value=0):
        return {'value': value + 1}

As long as the module is imported when the pyboard boots,
:meth:`@instruction <pyt.instruction>` will register the method it decorates
as a valid instruction.

More examples of this are documented in: :ref:`examples.components`


Serialised Format
------------------

Each argument given to an instruction is serialised and set to the pyboard.
The pyboard will respond with ``ok\r`` for every instruction it successfully
receives, de-serialises, and executes.

All data sent to and from the pyboard is serialised into :mod:`json`.

So if I were to execute::

    pyboard.ping(1, 2, x=3, y=4)

The following would be sent to the pyboard

.. code-block:: json

    {"i": "ping", "a": [1, 2], "k": {"x": 3, "y": 4}}

Where:

* ``i`` - instruction
* ``a`` - arguments
* ``k`` - key-word arguments

Of course, this wouldn't go well because the :meth:`ping() <upyt.cmd.test.ping>`
instruction is very simple, and won't accept these parameters.
