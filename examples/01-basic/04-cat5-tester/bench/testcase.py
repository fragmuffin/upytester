import upytester
import unittest

from .socket import RJ45Socket, SocketPin


class BenchTest(unittest.TestCase):
    """
    This bench simply has 2 sockets, connecting to each end of the _product_;
    the ethernet cable.
    One socket is used purely as stimulus, and the other for evaluation.
    """
    @classmethod
    def setUpClass(cls):
        super(BenchTest, cls).setUpClass()

        # Connect to PyBoards
        cls.pyb_a = upytester.project.get_device('pyb_a')

        # Create Sockets
        cls.socket_stim = RJ45Socket(
            pins=[
                SocketPin(cls.pyb_a, 'Y5'),
                SocketPin(cls.pyb_a, 'Y6'),
                SocketPin(cls.pyb_a, 'Y7'),
                SocketPin(cls.pyb_a, 'Y8'),
                SocketPin(cls.pyb_a, 'X9'),
                SocketPin(cls.pyb_a, 'X10'),
                SocketPin(cls.pyb_a, 'X11'),
                SocketPin(cls.pyb_a, 'X12'),
            ],
            mode='stim',
        )
        cls.socket_eval = RJ45Socket(
            pins=[
                SocketPin(cls.pyb_a, 'Y12'),
                SocketPin(cls.pyb_a, 'Y11'),
                SocketPin(cls.pyb_a, 'Y10'),
                SocketPin(cls.pyb_a, 'Y9'),
                SocketPin(cls.pyb_a, 'X8'),
                SocketPin(cls.pyb_a, 'X7'),
                SocketPin(cls.pyb_a, 'X6'),
                SocketPin(cls.pyb_a, 'X5'),
            ],
            mode='eval',
        )

    #@classmethod
    #def tearDownClass(cls):
    #    super(BenchTest, cls).tearDownClass()

    def setUp(self):
        # Set all output socket pins low
        for i in range(self.socket_stim.pin_count):
            self.socket_stim.pin_value(i, 0)

    def tearDown(self):
        # Set all output socket pins low
        for i in range(self.socket_stim.pin_count):
            self.socket_stim.pin_value(i, 0)
