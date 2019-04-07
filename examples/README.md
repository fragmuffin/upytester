# Examples

Each of the folders in this directory contains multiple example "projects"
made in an attempt to showcase the original intent of this library, and how
to use it.

## `01-Basic`

Examples to cover the absolute basics of `upytester`.\
They are designed to introduce as few new concepts as possible from one to
the next if followed in sequence.

* PyBoard setup, sync, and basic serial communication
* LED stimulus
* `USR` button evaluation
* Network Cable Tester
* CAN Bus

## `02-On-Board-Components`

Examples of custom simulated components running on one or more of the
pyboards themselves.\
This is often necessary to effectively simulate close to real behaviour of
the components being simulated. Utilising the real-time nature of the
pyboards, utilising interrupts, asyncio scheduler, effective network
communication, among other resources may all be necessary for your project.

* Contactor
* Accurate timing evaluation using an interrupt
* Cyclic CAN frame sequential counter

## `03-Sample-Project`

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
