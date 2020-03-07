import unittest
import upytester

# Uncomment for verbose output
#import logging
#logging.basicConfig(level=logging.DEBUG)


class ReactionTimeTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.pyb_a = upytester.project.get_device('pyb_a')
        self.led = self.pyb_a.MyLED(2)

    @classmethod
    def tearDownClass(self):
        self.pyb_a.close()

    def test_blink_func(self):
        """Run async function."""
        self.pyb_a.async_blink(1)

    def test_blink_remote(self):
        """Create object and run async function."""
        self.led.blink()
