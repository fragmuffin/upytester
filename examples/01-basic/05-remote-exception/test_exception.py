import unittest
import upytester

# Uncomment to observe serial communication
import logging
import sys
#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class ExceptionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pyb_a = upytester.project.get_device('pyb_a')

    @classmethod
    def tearDownClass(cls):
        cls.pyb_a.close()

    def test_bad_ping_sync(self):
        """
        Send a ping command, with str() instead of an int().
        """
        receiver = self.pyb_a.ping(value='abc')
        response = receiver()

    def test_bad_ping_async(self):
        """
        Send a ping command, with str() instead of an int().
        """
        self.pyb_a.async_tx = True
        receiver = self.pyb_a.ping(value='abc')
        response = receiver()
        self.pyb_a.async_tx = False

    def test_bad_ping_synclist(self):
        """
        Send a series of pings synchronously, one of the requests is invalid.
        """
        # Send request, and block until response is received
        self.pyb_a.ping(value=10)
        self.pyb_a.ping(value=20)
        self.pyb_a.ping(value=30)
        self.pyb_a.ping(value='xyz')  # bad code
        self.pyb_a.ping(value=40)
        self.pyb_a.ping(value=50)
        self.pyb_a.ping(value=60)

        self.assertEqual(
            [self.pyb_a.receive()['value'] for i in range(6)],
            [11, 21, 31, 41, 51, 61]
        )

    def test_bad_ping_asynclist(self):
        """
        Send a series of pings synchronously, one of the requests is invalid.
        """
        self.pyb_a.async_tx = True

        # Push requests to a FIFO stack, sent in sequence by a thread
        self.pyb_a.ping(value=10)
        self.pyb_a.ping(value=20)
        self.pyb_a.ping(value=30)
        self.pyb_a.ping(value='xyz')  # bad code
        self.pyb_a.ping(value=40)
        self.pyb_a.ping(value=50)
        self.pyb_a.ping(value=60)

        self.assertEqual(
            [self.pyb_a.receive()['value'] for i in range(6)],
            [11, 21, 31, 41, 51, 61]
        )

        self.pyb_a.async_tx = False
