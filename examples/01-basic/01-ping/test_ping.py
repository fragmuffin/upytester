import unittest
import upytester

class PingTest(unittest.TestCase):
    def setUp(self):
        """
        Executed just before each test of this class.

        Creates a :class:`PyBoard <upytester.PyBoard>` instance as ``self.pyb_a``.

        Each connected pyboard is identified on the host's USB bus by its
        serial number, as defined in the ``.upytester-config.yml`` file.

        see `setUp() documentation <https://docs.python.org/3.7/library/unittest.html#unittest.TestCase.setUp>`_
        for details.
        """
        self.pyb_a = upytester.project.get_device('pyb_a')

    def tearDown(self):
        """
        Executed just after each test of this class.

        Closes the serial link to ``self.pyb_a``.

        see `tearDown() documentation <https://docs.python.org/3.7/library/unittest.html#unittest.TestCase.tearDown>`_
        for details.
        """
        self.pyb_a.close()

    def test_ping(self):
        """
        Send a ping request over serial to the pyboard identified as ``pyb_a``.

        """
        receiver = self.pyb_a.ping(value=100)
        response = receiver()
        self.assertEqual(response['value'], 101)  # ping sends back value + 1
