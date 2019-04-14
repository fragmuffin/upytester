import time
import unittest
import upytester


# ------------ Bench Environment ------------
class Switch(object):
    def __init__(self, device):
        self.device = device

    @property
    def value(self):
        return self.device.get_switch()()['value']


class BenchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pyb_a = upytester.project.get_device('pyb_a')
        cls.switch = Switch(device=cls.pyb_a)

    @classmethod
    def tearDownClass(cls):
        cls.pyb_a.close()


# ------------ Tests ------------

class SwitchTest(BenchTest):
    def test_switch_pressed(self):
        """
        Turn red LED on for 500ms asynchronously
        """
        self.assertTrue(self.switch.value)
