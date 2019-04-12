import time
import unittest
import upytester


class BenchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pyb_a = upytester.project.get_device('pyb_a')

    @classmethod
    def tearDownClass(cls):
        cls.pyb_a.close()


class LEDTest(BenchTest):

    def test_blink(self):
        """
        Turn red LED on for 500ms asynchronously
        """
        self.pyb_a.blink_led(duration=500)
        time.sleep(0.5)  # just wait so tests don't run at the same time

    def test_led_set(self):
        """
        Turn green LED on for
        """
        self.pyb_a.set_led(led=2)
        time.sleep(0.5)
        self.pyb_a.set_led(led=2, intensity=0)
