import unittest
import upytester

class ExceptionTest(unittest.TestCase):
    def setUp(self):
        self.pyb_a = upytester.project.get_device('pyb_a')

    def tearDown(self):
        self.pyb_a.close()

    def test_bad_ping(self):
        """
        Send a ping command, with str() instead of an int().
        """
        receiver = self.pyb_a.ping(value='abc')
        response = receiver()
