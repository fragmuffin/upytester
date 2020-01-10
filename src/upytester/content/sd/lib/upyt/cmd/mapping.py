"""Decorators and inherant upyt instructions for querying."""
import json
import gc

from .types import type_gen_func, type_func

# -------------- Instructions --------------
_instruction_map = {}


def instruction(func):
    r"""
    Map a function to an incoming instruction.

    Usage::

        @instruction
        def ping(value=0):
            return {'r': 'ping', 'value': value + 1}

    With this implemented, when a host sends
    ``{'i': 'ping', 'k': {'value': 10}}``, it will receive
    ``{'r': 'ping', 'value': 11}``

    **Format of Request**
    When transmitting a request from a host machine, the ``dict`` format is::

        {
            'i': 'some_instruction',  # name of the method
            'a': [1, 'abc', -5.4],  # optional list arguments
            'k': {  # optional keywords argument list
                'value': True,
                'pin': 'X3',
            }
        }

    **Instruction Design for Serializing**\
    Because the method name, and keyword arguments are serialized and
    transmitted, consider keeping argument & method names short.
    """
    if not isinstance(func, (type_func, type_gen_func)):
        raise ValueError("{!r} is not a method".format(func))
    if func.__name__ in _instruction_map:
        raise ValueError("duplicate instruction; can't replace {old!r} with {new!r}".format(  # noqa: E501
            old=_instruction_map[func.__name__], new=func,
        ))
    _instruction_map[func.__name__] = func
    return func


@instruction
def list_instructions():
    """List functions decorated as instructions."""
    return sorted(_instruction_map.keys())


# -------------- Remote Objects --------------
_remote_class_map = {}
_remote_instance_map = {}
_remote_instance_index = 0


def remote(cls):
    """
    Map a class as being accessible via remote instance.

    To create a remote class on the pyboard::

        import pyb
        from upyt.mapping import remote

        @remote
        class Pin:
            def __init__(self, name, mode='in')
                self._pin = pyb.Pin(
                    name,
                    pyb.Pin.OUT if mode == 'out' else pyb.Pin.IN,
                )

            def value(self, v=None):
                return self._pin.value(v)

            def high(self):
                self.value(True)

            def low(self):
                self.value(False)

    Then, to create and access a remote instance from the tester PC::

        import unittest
        import upytester

        class TestPin(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                cls.pyb_a = upytester.project.get_device('pyb_a')
                cls.my_pin = cls.pyb_a.Pin('X1', mode='in')

            def test_pin_stuff(self):
                self.pin.value(1)
                self.assertTrue(self.pin.value())
                self.pin.value(0)
                self.assertFalse(self.pin.value())
    """
    if cls.__name__ in _remote_class_map:
        raise ValueError("duplicate remote class; can't replace {old!r} with {new!r}".format(  # noqa: E501
            old=_remote_class_map[cls.__name__], new=cls,
        ))
    _remote_class_map[cls.__name__] = cls
    return cls


@instruction
def list_remote_classes():
    """List classes decorated as remotes."""
    return sorted(_remote_class_map.keys())


@instruction
def clean_remote_classes():
    """Remove all instances from map and re-claim memory."""
    while _remote_instance_map:
        for (i, obj) in _remote_instance_map.items():
            del_func = getattr(obj, '__del__', None)
            if del_func:
                del_func()
            del _remote_instance_map[i]
        gc.collect()
    # note: _remote_instance_index is NOT reset to mitigate the risk of
    #       re-using a cleaned object on the host, and inadvertently
    #       invoking another that's been created since.


_GET_OBJ_REF_FORMAT_MSG = "object reference must be of the format: " \
                          "{'cls': <class name>, 'idx': <remote index int>}"


def _assert_get_obj_ref(ref):
    assert isinstance(ref, dict), _GET_OBJ_REF_FORMAT_MSG
    assert set(ref.keys()) == {'cls', 'idx'}, _GET_OBJ_REF_FORMAT_MSG
    assert isinstance(ref['cls'], str), _GET_OBJ_REF_FORMAT_MSG
    assert isinstance(ref['idx'], int), _GET_OBJ_REF_FORMAT_MSG


def get_obj(ref: dict, *args):
    """
    Get a remotely set object from it's reference dict.

    :param ref: :class:`dict` of the form:
                ``{'cls': <class name>, 'idx': <remote index>}``
    :param default: default value to return if object
                    cannot be found [optional]
    """
    try:
        """Convert serialised reference into local object instance."""
        _assert_get_obj_ref(ref)
        obj = _remote_instance_map[ref['idx']]
        if type(obj).__name__ != ref['cls']:
            raise TypeError("Referenced object {!r} is of a different type {!r}".format(ref, type(obj)))  # noqa: E501
        return obj
    except Exception:
        if args:
            assert len(args) == 1, "only 1 [optional] default can be given"
            return args[0]  # give default
        raise  # no default specified, be strict.


# -------------- Interpreter --------------
_serial_port = None


def set_serial_port(given_port):
    """
    Set the serial object through which to send serialized data.

    See :meth:`send` for more details.

    :param given_port: Port through which to send serialized data
    :type given_port: :class:`pyb.USB_VCP`
    """
    global _serial_port
    _serial_port = given_port


def send(obj):
    """
    Send serial data over the preset serial port.

    Usage:

        >>> import pyb
        >>> from cmd import set_serial_port, send

        # Setup Port
        >>> com_port = pyb.USB_VCP()
        >>> set_serial_port(com_port)

        # Sender transmits json encoding of given obj over VCP
        >>> send('abc')
        >>> send(123)
        >>> send([1, 2, 3])
        >>> send({'a': 1, 'b': 2})
    """
    global _serial_port
    _serial_port.write(json.dumps(obj).encode() + b'\r')
