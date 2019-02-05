import serial
import json
import time

# Threads
import threading
import queue

# Local libs
from .map import get_pyboard_map

# Logging
import logging
log = logging.getLogger(__name__)


class PyBoard(object):
    # Timeouts
    #   maximum timeout value is the max time to wait for threads to finish.
    READ_TIMEOUT = 0.1  # maximum time per read (unit: sec
    READ_CHUNKSIZE = 1  # maximum bytes to receive

    WRITE_TIMEOUT = 0.1 # maximum time to wait while reading transmit queue

    RESPONSE_TIMEOUT = 1

    # Defaults
    DEFAULT_BAUDRATE = 115200

    class ResponseTimeoutException(Exception):
        """Raised when no 'ok' response is received from the pyboard"""
        pass

    def __init__(self, serial_number, comport=None, auto_open=True):
        self.serial_number = serial_number

        if comport is None:
            pyboard_map = get_pyboard_map()
            comport = serial.Serial(
                port=pyboard_map[serial_number]['port'].device,
                baudrate=self.DEFAULT_BAUDRATE,
            )
        self.comport = comport

        # Events
        self._halt_transmit = threading.Event()
        self._halt_receive = threading.Event()
        self._processing_transmit = threading.Event()

        self._open_flag = False

        # Queues
        self._receive_queue = queue.Queue()
        self._receive_ok_queue = queue.Queue()
        self._transmit_queue = queue.Queue()

        # Instruction List
        self._instruction_list = None

        if auto_open:
            self.open()

    @property
    def is_open(self):
        return self._open_flag

    @property
    def is_closed(self):
        return not self._open_flag

    def open(self):
        if self.is_open:
            return  # already open

        # Open comport
        if self.comport.closed:
            self.comport.open()
        self.comport.timeout = self.READ_TIMEOUT
        while self.comport.read():
            pass  # flush

        # clear halt events
        self._halt_receive.clear()
        self._halt_transmit.clear()

        # actively transmitting event
        self._processing_transmit.clear()

        # ----- Receiver thread
        # empty queue
        while not self._receive_queue.empty():
            self._receive_queue.get(block=False)  # discard entries

        def receiver_proc():
            """
            Puts lines onto the received queue.

            :param chunk_size: maximum number of bytes in each chunk
            :type chunk_size: :class:`int`
            """
            # Line iterator (why? encapsulating mess)
            def line_iter(end_on_timeout=False):
                # yields each line (not including line end character)
                line = b''
                while not self._halt_receive.is_set():
                    chunk = self.comport.read(self.READ_CHUNKSIZE)
                    if chunk:
                        #log.debug("%r --> (chunk) %r", self, chunk)
                        while chunk:
                            i = chunk.find(b'\r')
                            if i >= 0:
                                line += chunk[:i]
                                chunk = chunk[i+1:]
                                yield line
                                line = b''
                            else:
                                line += chunk
                                chunk = b''
                    elif end_on_timeout:
                        break

            # One loop per line
            error_state = False
            try:
                for line in line_iter():
                    log.debug("%r --> %r", self, line)
                    if line == b'ok':
                        # separate 'ok' receiver queue (as responses to received requests)
                        self._receive_ok_queue.put(line)
                    else:
                        # everything else
                        obj = json.loads(line.rstrip(b'\r'))
                        if obj is None:  # ie: json.loads('null')
                            raise ValueError(
                                ("Received '%s' from remote which decodes to 'None', " % line) +
                                "this is a reserved value and should not be transmitted by a remote"
                            )

                        self._receive_queue.put(obj)
            except json.decoder.JSONDecodeError:
                # a JSON decoding error could be because the pyboard has hit
                # an exception, and returned to a REPL.
                # This will cause the pyboard-based exception error text to be send
                # over serial... so we should print out the tntire queue
                def _err_line_gen():
                    yield line  # this is the line that initially failed
                    for l in line_iter(end_on_timeout=True):
                        yield l

                log.error("ERROR from pyboard: {}".format(self.serial_number))
                for l in _err_line_gen():
                    log.error('  {}'.format(l.decode().lstrip('\r\n').rstrip('\r\n')))
                raise

        # start process
        self._receive_thread = threading.Thread(
            target=receiver_proc,
            name='{!r} receiver'.format(self),
        )
        self._receive_thread.daemon = True  # kills thread when main process dies
        self._receive_thread.start()

        # ----- Transmitter thread
        def transmit_proc():
            while not (self._halt_transmit.is_set() and self._transmit_queue.empty()):
                try:
                    # Send request
                    line = self._transmit_queue.get(timeout=self.WRITE_TIMEOUT)
                    self._processing_transmit.set()
                    log.debug("%r <-- %r", self, line)
                    self.comport.write(line)

                    # Block until response (or timeout & fail)
                    try:
                        response = self._receive_ok_queue.get(timeout=self.RESPONSE_TIMEOUT)
                        # note: nothing done with response (yet)
                    except queue.Empty:
                        raise self.ResponseTimeoutException("{!r}".format(self))
                    finally:
                        if self._transmit_queue.empty():
                            self._processing_transmit.clear()

                except queue.Empty:
                    continue

            self._halt_receive.set()

        # start process
        self._transmit_thread = threading.Thread(
            target=transmit_proc,
            name='{!r} transmitter'.format(self),
        )
        self._transmit_thread.daemon = True  # kills thread when main process dies
        self._transmit_thread.start()

        # populate instruction_list
        self.instruction_list  # getting it populates it, but don't do anything with it.

        # set flag
        self._open_flag = True

    def halt(self):
        self._halt_transmit.set()

    def close(self):
        if self.is_closed:
            return  # already closed

        # set halt event
        self._halt_transmit.set()
        # receiver halt will be set by end of transmit process

        # wait for threads to complete
        self._transmit_thread.join()
        self._receive_thread.join()

        # close comport
        if not self.comport.closed:
            self.comport.close()

        # clear instruction list
        self._instruction_list = None

    @property
    def instruction_list(self):
        if self._instruction_list is None:
            self.send({'i': 'list_instructions'})
            self._instruction_list = self.receive(timeout=0.1)
        return self._instruction_list

    def __repr__(self):
        return "<{cls}: {serial}>".format(
            cls=type(self).__name__,
            serial=self.serial_number,
        )

    def __getattr__(self, key):
        if (self._instruction_list is not None) and (key in self._instruction_list):
            # Create a callable that will send apropriately formatted object
            def instruction(*args, **kwargs):
                obj = kwargs
                if args:
                    obj['args'] = args
                obj['i'] = key
                return self.send(obj)

            instruction.__name__ = key
            return instruction

        raise AttributeError("'{}' object has no attribute '{}'".format(type(self).__name__, key))

    def send(self, obj):
        """
        Transmit given object encoded as json
        :param obj: object to json encode and transmit
        :type obj: anthing serializable
        """
        if self._halt_transmit.is_set():
            raise RuntimeError("Cannot send more commands while {!r} is being closed".format(self))

        line = json.dumps(obj, separators=(',',':')).encode()
        self._transmit_queue.put(line + b'\r')  # will be picked up and processed by self._transmit_thread

        # return receiver method
        return self.receive

    def receive(self, timeout=None):
        """
        Receive object from remote.

        If ``timeout`` is set, and nothing is received, ``None`` is returned
        after ``timeout``.

        :param timeout: Time to wait for a response (if ``None``, will wait forever).
                        If timeout is reached, ``None`` is returned.
        :type timeout: :class:`float`
        :return: decoded json object
        :rtype: :class:`dict`, or ``None``
        """
        try:
            obj = self._receive_queue.get(timeout=timeout)
            return obj
        except queue.Empty:
            return None

    def receive_iter(self, timeout=None):
        """
        Generator for each received object.

        :param timeout: Maximum time per iteration, if not set, only received
                        objects will be returned.
        :type timeout: :class:`float`
        """
        while True:
            yield self.receive(timeout=timeout)

    def wait(self, period=0.05):
        """
        Wait for transmit queue to be clear, meaning everything in the transmit
        queue has been sent and ok'd by the remote.

        :param period: polling period (seconds)
        :type period: :class:`float`
        """
        # FIXME: this is just polling, is there a better way to block until queue is empty?
        while not (self._transmit_queue.empty() and not self._processing_transmit.is_set()):
            time.sleep(period)
