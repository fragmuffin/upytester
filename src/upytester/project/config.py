import os
import yaml

# Constants (sort of)
DEFAULT_CONFIG_FILENAME = '.upytester.yml'


def get_config(filename=None):
    # Default parameter value(s)
    if filename is None:
        # Check local directory
        if os.path.isfile(DEFAULT_CONFIG_FILENAME):
            filename = DEFAULT_CONFIG_FILENAME
        else:
            # Check home directory
            _home_filename = os.path.join(
                os.path.expanduser('~'),
                DEFAULT_CONFIG_FILENAME
            )
            if os.path.isfile(_home_filename):
                filename = _home_filename

    # Decode
    with open(filename, 'r') as fh:
        data = yaml.safe_load(fh)

    return data


def get_device(name, config=None):
    """
    Get a PyBoard device by name, configured in the project.

    :param name: PyBoard named in configuration file
    :type name: :class:`str`
    """
    if config is None:
        config = get_config()

    from ..pyboard import PyBoard
    return PyBoard(
        serial_number=config['devices'][name]['serial'],
        name=name,
    )
