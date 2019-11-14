import time
import unittest
import upytester


class BenchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pyb_a = upytester.project.get_device('pyb_a')
        cls.red_led = cls.pyb_a.LED(1)
        cls.green_led = cls.pyb_a.LED(2)

    @classmethod
    def tearDownClass(cls):
        cls.pyb_a.clean_remote_classes()
        cls.pyb_a.close()


class LEDTest(BenchTest):

    def test_blink(self):
        """Turn red LED on for 500ms (non-blocking)."""
        self.red_led.blink(duration=500)
        time.sleep(0.5)  # just wait so tests don't run at the same time

    def test_led_set(self):
        """Turn green LED on for 500ms (blocking)."""
        self.green_led.on()
        time.sleep(0.5)
        self.green_led.off()
