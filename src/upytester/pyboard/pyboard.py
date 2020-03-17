import serial
import json
import time
import os

# Threads
import threading
import queue

# Local libs
from . import utils
from .exceptions import ResponseTimeoutException, PyBoardError

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
    WRITE_TIMEOUT = 0.1  # maximum time to wait while reading transmit queue
    RESPONSE_TIMEOUT = 1  # (unit: sec)

    # Defaults
    DEFAULT_BAUDRATE = 115200

    def __init__(self,
            serial_number,
            name=None,
            comport=None,
            comport_class=serial.Serial,
            auto_open=True,
            heartbeat=True,
        ):
        """
        :param serial_number: Serial number of PyBoard instance
        :type serial_number: :class:`str`
        :param name: Pyboard's Name [optional] to identify more easily in a
                     larger scale project.
        :type name: :class:`str`
        :param comport: serial stream (optional)
        :param comport_class: optional class to customize stream behaviour,
                              defaults to :class:`serial.Serial`

        To get a list of valid `serial_number` values call
        :meth:`<upytester.PyBoard.connected_serial_numbers> connected_serial_numbers`::

            >>> from upytester import PyBoard
            >>> list(PyBoard.connected_serial_numbers())
            ['3976346C3436', '397631234567']
        """
        self.serial_number = serial_number
        self.name = name

        # Events (all cleared by default)
        self._halt_transmit = threading.Event()
        self._halt_receive = threading.Event()
        self._not_transmitting = threading.Event()
        self._async_transmit = threading.Event()
        self._remote_exception = threading.Event()

        self._open_flag = False

        # Queues
        self._receive_queue = queue.Queue()
        self._receive_ok_queue = queue.Queue()
        self._transmit_queue = queue.Queue()
        self._remote_exception_queue = queue.Queue()

        # Instruction & Remote Class Lists
        self._instruction_list = None
        self._remote_class_list = None

        self.comport_class = comport_class
        self._comport = comport

        self._heartbeat = heartbeat

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
            self._comport = self.comport_class(
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

    @property
    def async_tx(self):
        return self._async_transmit.is_set()

    @async_tx.setter
    def async_tx(self, value):
        value = bool(value)  # cast to boolean
        if value == self._async_transmit.is_set():
            return  # do nothing

        # Wait for a break in transmission:
        #   Don't change exception reporting style half way through
        #   processing a stack of transmissions... wait until it's clear
        self._not_transmitting.wait()

        # Apply flag
        if value:
            self._async_transmit.set()
        else:
            self._async_transmit.clear()

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
        self._not_transmitting.set()

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
                    c = self.comport.read(1)
                    #log.debug("%r --> (c) %r", self, c)
                    if c:
                        if c == b'\r':
                            log.debug("{!r} --> {!r}".format(self, line))
                            yield line
                            line = b''
                        else:
                            line += c
                    elif end_on_timeout:
                        break

            # One loop per line
            error_state = False
            try:
                for line in line_iter():
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
                # over serial... so we should print out the entire queue
                self._remote_exception.set()

                # Collect exception stack trace line-by-line
                def _err_line_gen():
                    yield line  # this is the line that initially failed
                    for l in line_iter(end_on_timeout=True):
                        yield l

                msg_lines = ["{!r}".format(self)]
                for l in _err_line_gen():
                    msg_lines.append(
                        '  ' + l.decode().lstrip('\r\n').rstrip('\r\n')
                    )
                exception = PyBoardError('\n'.join(msg_lines))

                # Push received exception to
                #   - dedicated queue (for self.check_health() method)
                self._remote_exception_queue.put(exception)
                #   - receive queue (for quick response)
                if self._async_transmit.is_set():
                    self._receive_queue.put(exception)
                else:
                    if self._not_transmitting.is_set():
                        self._receive_queue.put(exception)
                    else:
                        self._receive_ok_queue.put(exception)

                self.halt(force=True)

        # start process
        self._receive_thread = threading.Thread(
            target=receiver_proc,
            name='{!r} receiver'.format(self),
        )
        self._receive_thread.daemon = True  # thread dies with main process
        self._receive_thread.start()

        # ----- Transmitter thread
        def transmit_proc():
            while not (self._halt_transmit.is_set() and self._transmit_queue.empty()):
                try:
                    # Send request
                    line = self._transmit_queue.get(timeout=self.WRITE_TIMEOUT)
                    log.debug("%r <-- %r", self, line)
                    self._not_transmitting.clear()
                    self.comport.write(line)

                    # Block until response (or timeout & fail)
                    if self._async_transmit.is_set():
                        # Pull the 'ok' from the queue, and continue.
                        #   If an exception is raiesd, it populates the
                        #   receive queue.
                        try:
                            response = self._receive_ok_queue.get(timeout=self.RESPONSE_TIMEOUT)
                            if isinstance(response, Exception):
                                raise response  # shouldn't happen
                        except queue.Empty:
                            if self._remote_exception.is_set():
                                # While expecting to receive an 'ok', we
                                # detected an exception on the host.
                                # That's why our receive request timed out
                                pass  # so do nothing
                            else:
                                raise ResponseTimeoutException("{!r}".format(self))
                        finally:
                            if self._transmit_queue.empty():
                                self._not_transmitting.set()
                    else:
                        # Wait for self.send() to indicate transmission completion
                        while not self._not_transmitting.wait(timeout=0.05):
                            if self._halt_transmit.is_set():
                                break  # handle halt case

                except queue.Empty:
                    continue

            self._halt_receive.set()

        # start process
        self._transmit_thread = threading.Thread(
            target=transmit_proc,
            name='{!r} transmitter'.format(self),
        )
        self._transmit_thread.daemon = True  # thread dies with main process
        self._transmit_thread.start()

        # --- Communication is open
        # populate lists
        self.instruction_list
        self.remote_class_list

        # show heartbeat (indicates link is active)
        if self._heartbeat:
            self.heartbeat(True)

        # set flag
        self._open_flag = True

    def check_health(self):
        """
        Check for any record of an exception being raised on the remote.

        :raises: :class:`PyBoardError`
        :return: True if no exception was found
        """
        if not self._remote_exception_queue.empty():
            raise self._remote_exception_queue.get(block=False)
        return True

    def halt(self, force=False):
        """
        Send a halt event to send and receive threads to cleanly stop.

        Timeouts may still need to play through, so the effect will not be
        instant.

        :param force: If ``True`` transmit queue is also emptied
        :type force: :class:`bool`


        """
        self._halt_transmit.set()
        if force:
            # Clean out transmit queue
            while not self._transmit_queue.empty():
                self._transmit_queue.get(block=False)

    def close(self):
        """
        Stop send and receive threads, and close comport.

        #. Calls :meth:`halt`
        #. Joins send & receive threads
        #. Closes ``self.comport``
        """
        if self.is_closed:
            return  # already closed

        # stop heartbeat (fault tolerant)
        if self._heartbeat:
            self.heartbeat(False)

        # set halt event
        self.halt()

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
        """List of names of instruction methods."""
        if self._instruction_list is None:
            self.send({'i': 'list_instructions'})
            self._instruction_list = self.receive(timeout=0.1)
        return self._instruction_list

    @property
    def remote_class_list(self):
        """List of names of remotely accessible classes."""
        if self._remote_class_list is None:
            self.send({'i': 'list_remote_classes'})
            self._remote_class_list = self.receive(timeout=0.1)
        return self._remote_class_list

    def _json_default_encoding(self, obj):
        if isinstance(obj, type(self).RemoteClass):
            if obj._pyboard is not self:
                raise ValueError("cannot pass remote object reference from {!r} to {!r}".format(obj._pyboard, self))  # noqa: E501
        if hasattr(obj, '__json__'):
            return obj.__json__()
        raise TypeError("Object of type '{}' is not JSON serializable".format(type(obj).__name__))  # noqa: E501

    def send(self, obj):
        """
        Transmit given object encoded as json.

        :param obj: object to json encode and transmit
        :type obj: anthing serializable
        """
        if self._halt_transmit.is_set():
            raise RuntimeError("Cannot send more commands while {!r} is being closed".format(self))  # noqa: E501

        line = json.dumps(
            obj,
            separators=(',', ':'),
            default=self._json_default_encoding,
        ).encode()
        # will be picked up and processed by self._transmit_thread
        self._transmit_queue.put(line + b'\r')

        if not self._async_transmit.is_set():
            # Non async transmission behaviour:
            #   The send function blocks until we receive:
            #       - 'ok' indicating success on the remote
            #       - an exception with details of what went wrong.
            try:
                response = self._receive_ok_queue.get(timeout=self.RESPONSE_TIMEOUT)
                if isinstance(response, Exception):
                    raise response
            except queue.Empty:
                raise ResponseTimeoutException("{!r}".format(self))
            finally:
                if self._transmit_queue.empty():
                    self._not_transmitting.set()

        # return receiver method
        return self.receive

    def receive(self, timeout=1):
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
            if isinstance(obj, Exception):
                raise obj
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
        while not (self._transmit_queue.empty() and self._not_transmitting.is_set()):
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
            time.sleep(2.5)  # wait reasonable time for USB to re-connect to OS
        else:
            self.comport.write(b'\x03\x04')  # [Ctrl+C] + [Ctrl+D]
            self.comport.close()
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

    @staticmethod
    def _payload(payload, *args, **kwargs):
        if args:
            payload['a'] = args
        if kwargs:
            payload['k'] = kwargs
        return payload

    def __getattr__(self, key):
        # --- Instruction
        is_instruction = all((
            self._instruction_list is not None,
            key in self._instruction_list,
        ))
        if is_instruction:
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

        # --- Remote Class
        is_remote_class = all((
            self._remote_class_list is not None,
            key in self._remote_class_list,
        ))
        if is_remote_class:
            # Create instance of object on pyboard.
            def constructor(*args, **kwargs):
                payload = self._payload({'rc': key}, *args, **kwargs)
                return type(key, (type(self).RemoteClass,), {})(
                    self, self.send(payload)()
                )
            return constructor

        raise AttributeError("'{}' object has no attribute '{}'".format(
            type(self).__name__, key
        ))

    class RemoteClass:
        """Enables access to an instance on a remote."""

        def __init__(self, pyboard, idx):
            self._pyboard = pyboard
            self._idx = idx

        def __repr__(self):
            return "<{cls}: @remote[{idx}] on {pyboard!r}>".format(
                cls=self.__class__.__name__,
                idx=self._idx,
                pyboard=self._pyboard,
            )

        def __getattr__(self, key):
            def func(*args, **kwargs):
                payload = self._pyboard._payload(
                    {'rid': self._idx, 'i': key}, *args, **kwargs
                )
                return self._pyboard.send(payload)
            func.__name__ = key
            return func

        def __json__(self):
            """Serialise for transmission to a remote."""
            return {
                'cls': type(self).__name__,
                'idx': self._idx,
            }
