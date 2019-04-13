import unittest
import upytester

class PingTest(unittest.TestCase):
    def setUp(self):
        self.pyb_a = upytester.project.get_device('pyb_a')

    def tearDown(self):
        self.pyb_a.close()

    def test_ping(self):
        """
        Send a ping request over serial to the pyboard identified as ``pyb_a``.
        """
        receiver = self.pyb_a.ping(value=100)
        response = receiver()
        self.assertEqual(response['value'], 101)  # ping sends back value + 1
