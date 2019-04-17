import serial
import json
import time
import os

# Threads
import threading
import queue

# Local libs
from . import utils
from .exceptions import ResponseTimeoutException

# Logging
import logging
log = logging.getLogger(__name__)


class PyBoard(object):
    """
    The primary interface to a physical device running the `upytester`
    firmware.

    Can also be used more passively to mount / unmount file-systems, get
    the device's mountpoint (a folder name)
    """

    # Timeouts
    #   maximum timeout value is the max time to wait for threads to finish.
    READ_TIMEOUT = 0.1  # maximum time per read (unit: sec)
    READ_CHUNKSIZE = 1  # maximum bytes to receive

    WRITE_TIMEOUT = 0.1 # maximum time to wait while reading transmit queue

    RESPONSE_TIMEOUT = 1

    # Defaults
    DEFAULT_BAUDRATE = 115200

    def __init__(self, serial_number, name=None, comport=None, auto_open=True):
        """
        :param serial_number: Serial number of PyBoard instance
        :type serial_number: :class:`str`
        :param name: Pyboard's Name [optional] to identify more easily in a
                     larger scale project.
        :type name: :class:`str`

        To get a list of valid `serial_number` values call
        :meth:`<upytester.PyBoard.connected_serial_numbers> connected_serial_numbers`::

            >>> from upytester import PyBoard
            >>> list(PyBoard.connected_serial_numbers())
            ['3976346C3436', '397631234567']
        """
        self.serial_number = serial_number
        self.name = name

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

        self._comport = comport

        if auto_open:
            self.open()

    # ==================== OS-level Management ====================
    # Such as:
    #   - Listing units connected to host
    #   - Mounting / Unmounting file-systems (sd / flash)
    @classmethod
    def connected_serial_numbers(cls):
        return utils.connected_serial_numbers()

    # ----- SD Card
    def mount_sd(self):
        """
        Mount SD card

        :return: path to mounted folder
        :rtype: :class:`str`
        """
        return utils.mount_sd(self)

    def unmount_sd(self):
        """
        Unmount SD card
        """
        return utils.unmount_sd(self)

    @property
    def mountpoint_sd(self):
        """
        Directory of mounted SD card
        """
        return utils.find_mountpoint_sd(self)

    def sync_to_sd(self, source, **kwargs):
        """
        Synchronise files from the given `source` to the pyboard's SD card

        :param source: Directory containing files to syncronise _to_ pyboard
        :type source: :class:`str`
        :param force: If `True`, assertion of the pre-existence of placeholder
                      files will be ignored.
        :type force: :class:`bool`
        :param dryrun: If `True`, sync will not be performed, but everything else
                       will be done. Use to manually confirm folder sync if
                       you're concerned about what it'll do.
        :type dryrun: :class:`bool`
        :param quiet: If `True` process will not print anything to stdout
        :type quiet: :class:`bool`
        """
        self.mount_sd()
        return utils.sync_files_to_sd(source, self, **kwargs)
        self.unmount_sd()

    # ----- Flash
    def mount_flash(self):
        """
        Mount on-board flash

        :return: path to mounted folder
        :rtype: :class:`str`
        """
        return utils.mount_flash(self)

    def unmount_flash(self):
        """
        Unmount on-board flash
        """
        return utils.unmount_flash(self)

    @property
    def mountpoint_flash(self):
        """
        Directory of mounted on-board flash
        """
        return utils.find_mountpoint_flash(self)

    def sync_to_flash(self, source, **kwargs):
        """
        Just like :meth:`PyBoard.sync_to_sd` but to Flash
        (instead of the SD card).
        """
        self.mount_flash()
        return utils.sync_files_to_flash(source, self, **kwargs)
        self.unmount_flash()

    # ==================== Serial Communication ====================
    @property
    def comport(self):
        if self._comport is None:
            port_info = utils.find_portinfo(self)
            self._comport = serial.Serial(
                port=port_info.device,
                baudrate=self.DEFAULT_BAUDRATE,
            )

        return self._comport

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
                        obj = json.loads(line.rstrip(b'\r').decode())
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

                log.error("ERROR from pyboard: {!r}".format(self))
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
                        raise ResponseTimeoutException("{!r}".format(self))
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

    def reset(self, hard=False):
        """
        **Soft Reset**

        A soft reset invokes the :meth:`machine_reset` method by using the
        onboard ``upytester`` library. Obviously this will only work if there
        is funcitonal ``upytester`` firmware running on the pyboard's SD card.

        **Hard Reset**

        A Ctrl+C character ``ext`` is sent to simulate a :class:`KeyboardInterrupt`
        exception. Then, assuming a REPL has started on the pyboard, these
        commands are sent::

            import pyb
            pyb.hard_reset()

        :param hard: if ``True``, a hard reset is performed, soft by default
        :type hard: :class:`bool`
        """
        if hard:
            self.comport.write(b'\x03\r\nimport pyb\r\npyb.hard_reset()\r\n')
            self.comport.close()
        else:
            self.machine_reset(t=500)
            self.close()
        self._comport = None

    # ==================== Context Management ====================
    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    # ==================== Housekeeping ====================
    def __repr__(self):
        return "<{cls}[{serial}]{name}>".format(
            cls=type(self).__name__,
            serial=self.serial_number,
            name=(": {}".format(self.name)) if self.name else "",
        )

    def __getattr__(self, key):
        if (self._instruction_list is not None) and (key in self._instruction_list):
            # Create a callable that will send apropriately formatted object
            def instruction(*args, **kwargs):
                payload = {'i': key}
                if args:
                    payload['a'] = args
                if kwargs:
                    payload['k'] = kwargs
                return self.send(payload)
            instruction.__name__ = key  # function has key name

            return instruction

        raise AttributeError("'{}' object has no attribute '{}'".format(type(self).__name__, key))
