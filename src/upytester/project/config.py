import yaml


# Constants (sort of)
DEFAULT_CONFIG_FILENAME = '.upytester-config.yml'

def get_config(filename=None):
    # Default parameter value(s)
    if filename is None:
        filename = DEFAULT_CONFIG_FILENAME

    # Decode
    with open('.upytester-config.yml', 'r') as fh:
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
