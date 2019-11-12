"""Decorators and inherant upyt instructions for querying."""
import json
import gc


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
    assert isinstance(func, type(lambda: None)), "must decorate a function"
    assert func.__name__ not in _instruction_map, "duplicate instruction defined"  # noqa: E501
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
    assert isinstance(cls, type), "must decorate a class"
    assert cls.__name__ not in _remote_class_map, "duplicate remote defined"
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


def _get_obj_ver_iter(ref):
    yield isinstance(ref, dict)
    yield 'cls' in ref
    yield 'idx' in ref


def get_obj(ref):
    """Convert serialised reference into local object instance."""
    if not all(_get_obj_ver_iter(ref)):
        raise ValueError("cannot infer instance from reference: {!r}".format(ref))  # noqa: E501
    obj = _remote_instance_map[ref['idx']]
    if type(obj).__name__ != ref['cls']:
        raise TypeError("Referenced object {!r} is of a different type {!r}".format(ref, type(obj)))  # noqa: E501
    return obj


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


def interpret_instruction(obj: dict):
    """
    Interpret obj as arguments for the named instruction.

    ``obj`` must be of the format::

        {
            'i': <instruction name>,
            'a': <args list>,
            'k': <kwargs dict>,
        }

    For example::

        {'i': 'func_name', 'a': [10, 'abc'], 'k': {'x': 1, 'y': 2}}

    Will internally call the instruction ``func_name`` with::

        func_name(10, 'abc', x=1, y=2)

    Then transmit the returned value to the host (if not ``None``).
    """
    instruction_name = obj.get('i')
    if instruction_name not in _instruction_map:
        return

    # Execute function
    func = _instruction_map[instruction_name]
    response = func(*obj.get('a', []), **obj.get('k', {}))

    # Send response (if any given)
    if response is not None:
        send(response)


def interpret_new_remote_instance(obj: dict):
    """
    Interpret obj as constructor arguments for the named remote class.

    ``obj`` must be of the format::

        {
            'rc': <class name>,  # remote class
            'a': <args list>,
            'k': <kwargs dict>,
        }

    For example::

        {'rc': 'MyRemote', 'a': [10, 'abc'], 'k': {'x': 1, 'y': 2}}

    Will internally instantiate a new instance of ``MyRemote`` with::

        MyRemote(10, 'abc', x=1, y=2)

    Each instance will get a unique ID, and that ID will be send back to
    the host.

    Once an instance has been created, call upon it using
    :meth:`interpret_remote_instruction`.
    """
    global _remote_instance_index

    # Create Instance (assign unique id)
    cls = _remote_class_map[obj.get('rc')]
    instance = cls(*obj.get('a', []), **obj.get('k', {}))

    # Save to instance map
    instance._upyt_id = _remote_instance_index
    _remote_instance_index += 1
    _remote_instance_map[instance._upyt_id] = instance

    # Respond with instance ID
    send(instance._upyt_id)


def interpret_remote_instruction(obj: dict):
    """
    Interpret obj as a function call to an existing remote class instance.

    ``obj`` must be a :class:`dict` of the format::

        {
            'rid': <remote instance id>,  # remote id
            'i': <method name>,
            'a': <args list>,
            'k': <kwargs dict>,
        }

    When instantiating new instance of class::

        {'rid': 17, 'i': 'get_thing', 'a': [10, 'abc'], 'k': {'x': 1, 'y': 2}}

    Will call a previously instantiated remote which was given the id ``17``::

        internal_obj.get_thing(10, 'abc', x=1, y=2)

    Then transmit the returned value to the host (if not ``None``).
    """
    # Fetch remote instance from ID
    instance = _remote_instance_map[obj.get('rid')]
    #raise TypeError("instance is: {!r}".format(type(instance)))
    attr = getattr(instance, obj.get('i'))
    if callable(attr):
        response = attr(*obj.get('a', []), **obj.get('k', {}))
    else:
        response = attr

    # Send response (if any given)
    if response is not None:
        send(response)


def interpret(obj):
    """
    Perform the action defined in the given object.

    :param obj: deserialized JSON object received from host
    :type obj: :class:`dict`

    Given ``obj`` must be accepted by either :meth:`interpret_instruction`
    or :meth:`interpret_new_remote_instance`.
    """
    # Find referenced function
    if not isinstance(obj, dict):
        return

    if 'rid' in obj:
        interpret_remote_instruction(obj)
    elif 'rc' in obj:
        interpret_new_remote_instance(obj)
    elif 'i' in obj:
        interpret_instruction(obj)
    else:
        pass  # ignore instruction
