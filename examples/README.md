# Examples

Each of the folders in this directory contains multiple example "projects"
made in an attempt to showcase the original intent of this library, and how
to use it.

As a rule of thumb, all folders in this hierarchy that being with 2 numbers
(like `01-ping`) contains a sample project; a collection of files that
can be moved to another location and still work the same way.

My advice for beginners would be to copy one of these folders and paste it into
your project as a starting point.

**Running Examples**\
To execute an example, start a prompt and navigate into the directory, then
run `upytester` to execute.

```bash
cd 01-basic/01-ping
python runtests.py
```

## `01-basic`

Examples to cover the absolute basics of `upytester`.\
They are designed to introduce as few new concepts as possible from one to
the next if followed in sequence.

* [`01-ping`](01-basic/01-ping) - PyBoard setup, sync, and basic serial communication
* [`02-led-stimulus`](01-basic/02-led-stimulus) - Turn on an LED
* [`03-switch-evaluation`](01-basic/03-switch-evaluation) - `USR` button evaluation
* [`04-cat5-tester`](01-basic/04-cat5-tester) - Test a Cat 5 networking cable
* [`05-uart`](01-basic/05-uart) - Send and receive uart packets
* [`06-can-bus`](01-basic/06-can-bus) - Send and Receive CAN signals

## `02-on-board-components`

Examples of custom simulated components running on one or more of the
pyboards themselves.\
This is often necessary to effectively simulate close to real behaviour of
the components being simulated. Utilising the real-time nature of the
pyboards, utilising interrupts, asyncio scheduler, effective network
communication, among other resources may all be necessary for your project.

* [`01-contactor`](02-on-board-components/01-contactor) - Relay with feedback
* [`02-interrupt-eval`](02-on-board-components/02-interrupt-eval) - Accurate timing evaluation using an interrupt
* [`03-can-seq-signal`](02-on-board-components/03-can-seq-signal) - Cyclic CAN frame sequential counter

## `03-sample-project`

A contrived example of a "product" is designed for an Arduino Nano board.

Various components are included as part of the product:

* CAN shield
* Contactor (output to drive, input for feedback line)
* LED indicators
* PWM output to a servo motor
* Analog input for servo position

The project also has requirements to be verified, and test-cases
linking back to those requirements.\
This uses `doorstop` as a basic requirements management system.

Auxiliary hardware is used to interface with the _product_, schematics
and gerber files are all included.
