import pyb

from .mapping import instruction, send


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
