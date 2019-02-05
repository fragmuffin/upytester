import json

# -------------- Map Decorator --------------
_instruction_map = {}


def instruction(func):
    """
    Maps a function to an incoming instruction

    Usage::

        @instruction
        def ping(send, value=0):
            send({'r': 'ping', 'value': value + 1})

    With this implemented, when a host sends ``{'i': 'ping', 'value': 10}``,
    it will receive ``{'r': 'ping', 'value': 11}``

    **First Parameter**\
    The first parameter of the callback method is always ``send``, ``send`` will
    be a callable that can be used to transmit an object back to the host.

    **Format of Request**\
    When transmitting a request from a host machine, the ``dict`` format is::

        {
            'i': 'some_instruction',  # name of the method
            'args': [1, 'abc', -5.4],  # optional list arguments
            'value': True,  # remaining key:value pairs are used as keyword
                            # arguments.
            'pin': 'X3',
        }

    **Instruction Design for Serializing**\
    Because the method name, and keyword arguments are serialized and
    transmitted, consider keeping argument & method names short.
    """
    assert func.__name__ not in _instruction_map, "duplicate instruction defined"
    _instruction_map[func.__name__] = func
    return func


@instruction
def list_instructions(send):
    send(sorted(_instruction_map.keys()))

# -------------- Interpreter --------------

def get_sender(serial_port):
    """
    Returns callable to transmit objects over serial

    :param serial_port: com port instance
    :type serial_port: :class:`pyb.CAN_VCP`

    Usage::

        >>> from cmd import get_sender
        >>> com_port = pyb.USB_VCP()
        >>> send = get_sender(com_port)

        # Sender transmits json encoding of given obj over VCP
        >>> send('abc')
        >>> send(123)
        >>> send([1, 2, 3])
        >>> send({'a': 1, 'b': 2})
    """
    def send(obj):
        serial_port.write(json.dumps(obj).encode() + b'\r')
    return send


def interpret(sender_func, obj):
    """
    Perform the action defined in the given object

    :param sender_func: callable funtion for a reply
                        (ideally the callable returned by :meth:`get_sender`)
    :type sender_func: callable
    :param obj: deserialized JSON object received from host
    :type obj: :class:`dict`
    """

    if isinstance(obj, dict):
        instruction_name = obj.pop('i', None)
        if instruction_name in _instruction_map:
            func = _instruction_map[instruction_name]
            args = obj.pop('args', [])
            func(sender_func, *args, **obj)
