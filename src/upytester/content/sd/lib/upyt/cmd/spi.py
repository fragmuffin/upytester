import pyb
import struct

from asyn import Lock

from .mapping import remote


@remote
class SPI(pyb.SPI):
    """
    Remote of pyb.SPI.

    Offers some advantages over standard SPI object, including JSON
    serializable send/receive functions (prefixed with ``r_`` for _remote_).
    """
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

        self.bus = bus
        self.lock = Lock()

    def __del__(self):
        self.deinit()

    def __hash__(self):
        return self.bus

    @staticmethod
    def encode(data) -> bytes:
        """Encode data to be transmitted over SPI (into :class:`bytes`)."""
        if isinstance(data, bytes):
            return data
        elif isinstance(data, str):
            return data.encode()
        elif isinstance(data, int):
            return struct.pack('B', data)
        elif isinstance(data, list):
            return struct.pack('B' * len(data), *data)
        raise ValueError("cannot convert {!r} to bytes".format(data))

    # ----- Remote functions
    # Why not override core functions?
    #   send & receive data must be a bytes, memoryview, or an array, none of
    #   which will be decoded from a message from a remote.
    #   (ie: will not be an output of json.loads())
    def r_send(self, data, timeout: int=5000):
        """Transmit data, compatible with json encoding."""
        self.send(self.encode(data), timeout=timeout)

    def r_recv(self, count: int, timeout: int=5000):
        """Receive data, compatible with json encoding."""
        return list(self.recv(count, timeout=timeout))

    def r_send_recv(self, data, timeout: int=5000):
        """Transmit and receive data, compatible with json encoding."""
        return list(self.send_recv(self.encode(data), timeout=timeout))
