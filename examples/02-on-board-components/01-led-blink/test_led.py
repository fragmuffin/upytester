import unittest
import upytester

class LEDTest(unittest.TestCase):
    def setUp(self):
        self.pyb_a = upytester.project.get_device('pyb_a')

    def tearDown(self):
        self.pyb_a.close()

    def test_custom_blinker(self):
        """
        Test the on-board LED instruction
        """
        self.pyb_a.custom_blinker(led=3)
