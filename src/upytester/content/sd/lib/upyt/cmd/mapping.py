import json

# -------------- Map Decorator --------------
_instruction_map = {}


def instruction(func):
    """
    Maps a function to an incoming instruction

    Usage::

        @instruction
        def ping(value=0):
            return {'r': 'ping', 'value': value + 1}

    With this implemented, when a host sends ``{'i': 'ping', 'k': {'value': 10}}``,
    it will receive ``{'r': 'ping', 'value': 11}``

    **Format of Request**\
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
    assert func.__name__ not in _instruction_map, "duplicate instruction defined"
    _instruction_map[func.__name__] = func
    return func


@instruction
def list_instructions():
    return sorted(_instruction_map.keys())

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
    Send serial data over the preset serial port

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


def interpret(obj):
    """
    Perform the action defined in the given object

    :param obj: deserialized JSON object received from host
    :type obj: :class:`dict`
    """

    # Find referenced function
    if not isinstance(obj, dict):
        return

    instruction_name = obj.pop('i', None)
    if instruction_name not in _instruction_map:
        return

    # Execute function
    func = _instruction_map[instruction_name]
    response = func(*obj.pop('a', []), **obj.pop('k', {}))

    # Send response (if any given)
    if response is not None:
        send(response)
