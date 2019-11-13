import pyb
import struct

from .mapping import instruction
from .mapping import remote


@remote
class SPI(pyb.SPI):
    def __init__(self, bus, **kwargs):
        """
        :param bus: integer index of :class:`pyb.SPI` to use.
        :param mode: string, either ``'master'`` (default) or ``'slave'``.

        Also accepts :meth:`pyb.SPI.init` parameters
        (with the above exceptions)
        """
        super().__init__(bus)
        kwargs['mode'] = {
            'master': pyb.SPI.MASTER,
            'slave': pyb.SPI.SLAVE,
        }[kwargs.get('mode', 'master')]
        self.init(**kwargs)

    @staticmethod
    def _data2bytes(data):
        if isinstance(data, bytes):
            return data
        elif isinstance(data, str):
            return data.encode()
        elif isinstance(data, int):
            return struct.pack('B', data)
        elif isinstance(data, list):
            return struct.pack('B' * len(data), *data)
        raise ValueError("cannot convert {!r} to bytes".format(data))

    def send(self, data):
        """Transmit data."""
        self.send(self._data2bytes(data))

# ------- Map(s)
spi_map = {}  # {<idx>: <pyb.SPI>, ... }


# ------- Configure
@instruction
def config_spi(idx):
    """
    Configure SPI bus

    :param idx: pyboard SPI index (1 or 2)
    :type idx: :class:`int` (1 or 2)
    """
    spi = pyb.SPI(idx, pyb.SPI.MASTER)
    spi_map[idx] = spi


@instruction
def spi_send(idx, data):
    """
    Note: SPI must be configured via instruction :meth:`config_spi` before
    sending with this method.

    :param idx: pyboard SPI index (1 or 2)
    :type idx: :class:`int`
    :param data:
    :type data: :class:`list` of :class:`int`
    """
    spi = spi_map[idx]
    recv = spi.send_recv(bytes(data))
    # TODO: send received bytes
