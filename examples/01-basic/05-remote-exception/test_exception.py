import unittest
import upytester

import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

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
