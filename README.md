# UNDER CONSTRUCTION

This repository is under construction.

Much of what's written here is the targeted behaviour, but doesn't work yet.

Watch this space, and wait for the first release before using.

If you're interested in this project, please feel free to raise an issue
with your questions, even before the first release; I'm open to suggestions.

---

# `upytester`

Hardware test environment using MicroPython hardware as an interface.

## "What is `upytester`?"

`upytester` is a cpython library to facilitate running `unittest.TestCase`
tests on a host computer to stimulate and evaluate hardware via a
microcontroller running MicroPython.

## "What does a test bench look like?"

The host computer running the tests will inherit from `upytester.TestCase`
instead of `unittest.TestCase`.
This allows the host to seamlessly access GIPOs and various interfaces native
to the pyboard.

Each pyboard in the test environment is connected to the host via USB, allowing
a virtualised UART link between the host and each pyboard.


## "Why use `cPython`:`MicroPython`?"

Using micropython for stimulus and evaluation has the following advantages:

* Hardware is cheap
* Software is free
* All test code is in Python
* Tests can utilise real-time upython to stimulate and evaluate with very
  accurate timing.
* Custom models can be offloaded to pyboards
* Exceptions raised on a pyboard is reported to STDERR on the host (making
  debugging very easy)
* Expandable: if there isn't enough runtime on one pyboard, or you're running
  out of IO ports, just plug another pyboard in.

Many test-bench solutions require proprietary hardware and licensing to use
which can make a project very expensive.

It's also rare to find solutions for custom real-time behaviour that doesn't
create messy test code (if at all).


# Install

Installation is done in 2 stages, first the host, then use the host to connect
to your pyboards.

## Host

```bash
pip install upytester
```

## pyboard

Connect one or more pyboards via USB. To update all connected pyboards with the
most recent software.

```bash
python -m upytester update
```
