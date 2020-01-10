import uasyncio as asyncio
import json

from . import mapping
from .types import type_gen_func


async def interpret_instruction(obj: dict):
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
    if instruction_name not in mapping._instruction_map:
        return

    # Execute (async / non-async)
    func = mapping._instruction_map[instruction_name]
    if isinstance(func, type_gen_func):  # assumed async
        response = await func(*obj.get('a', []), **obj.get('k', {}))
    else:
        response = func(*obj.get('a', []), **obj.get('k', {}))

    # Send response (if any given)
    if response is not None:
        mapping.send(response)


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
    cls = mapping._remote_class_map[obj.get('rc')]
    instance = cls(*obj.get('a', []), **obj.get('k', {}))

    # Save to instance map
    instance._upyt_id = mapping._remote_instance_index
    mapping._remote_instance_index += 1
    mapping._remote_instance_map[instance._upyt_id] = instance

    # Respond with instance ID
    mapping.send(instance._upyt_id)


async def interpret_remote_instruction(obj: dict):
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
    instance = mapping._remote_instance_map[obj.get('rid')]

    # Get function as attribute of instance
    func = getattr(instance, obj.get('i'))
    if not callable(func):
        raise AttributeError("non-callable attributes are not supported")

    # Execute (async / non-async)
    if isinstance(func, type_gen_func):  # assumed async
        response = await func(*obj.get('a', []), **obj.get('k', {}))
    else:
        response = func(*obj.get('a', []), **obj.get('k', {}))

    # Send response (if any given)
    if response is not None:
        mapping.send(response)


async def interpret(obj):
    """
    Perform the action defined in the given object.

    :param obj: deserialized JSON object received from host
    :type obj: :class:`dict`

    Given ``obj`` must be accepted by either
    :meth:`interpret_instruction`,
    :meth:`interpret_new_remote_instance`, or
    :meth:`interpret_remote_instruction`.
    """
    # Find referenced function
    if not isinstance(obj, dict):
        return

    if 'rid' in obj:
        await interpret_remote_instruction(obj)
    elif 'rc' in obj:
        interpret_new_remote_instance(obj)
    elif 'i' in obj:
        await interpret_instruction(obj)
    else:
        pass  # ignore instruction


async def listener(stream):
    """Read and process lines from Virtual Comm Port (VCP)."""
    # TODO: create a global buffer, and populate via memoryview
    line = b''

    while True:
        c = stream.recv(1, timeout=0)  # non-blocking
        if c:
            if c == b'\r':
                # Interpret command, then respond with 'ok'
                #   Order is imporant:
                #       The host's transmit() method will block until it receives an 'ok'.
                #       With the interpret/response in this order, any exception raised
                #       while interpreting the object will cause the transmit() method
                #       to fail, causing the test itself to fail.
                #   Trade-off:
                #       This makes communication slightly slower, because the command has
                #       to complete before the host can begin to process the next command.
                #       However, it does enable tests to... you know... fail when they
                #       should. So the choice seems like a no-brainer.
                await interpret(json.loads(line))
                stream.write(b'ok\r')
                # Clear line
                line = b''
            else:
                line += c
        else:
            await asyncio.sleep_ms(1)
