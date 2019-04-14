import time
import unittest
import upytester


# ------------ Bench Environment ------------
class Socket(object):
    def __init__(self, device, pin, mode, value=None):
        self.device = device  # PyBoard instance
        self.pin = pin  # pin name (eg: 'X1')
        self.mode = mode  # 'stim' or 'eval'

        # Initialise Pin
        self.device.config_pin(
            id=self.pin,
            mode='out' if (self.mode == 'stim') else 'in',
            pull='down',
            value=value,
        )

    @property
    def value(self):
        return self.device.get_pin(self.pin)()['v']

    @value.setter
    def value(self, v):
        self.device.set_pin(self.pin, v)


class BenchTest(unittest.TestCase):
    PIN_MAP = {
        'STIM_SOCKET': 'X8',
        'EVAL_SOCKET': 'X9',
    }

    @classmethod
    def setUpClass(cls):
        # PyBoard device(s)
        cls.pyb_a = upytester.project.get_device('pyb_a')

        # Simulation / Evaluation Bench Components
        cls.wire_stim = Socket(
            device=cls.pyb_a,
            pin=cls.PIN_MAP['STIM_SOCKET'],
            mode='stim',
            value=0,
        )
        cls.wire_eval = Socket(
            device=cls.pyb_a,
            pin=cls.PIN_MAP['EVAL_SOCKET'],
            mode='eval',
        )

    @classmethod
    def tearDownClass(cls):
        cls.pyb_a.close()


# ------------ Tests ------------

class WireTest(BenchTest):
    def test_wire_low(self):
        """
        Signal connected as LOW
        """
        self.assertFalse(self.wire_stim.value)
        self.assertFalse(self.wire_eval.value)

    def test_wire_high(self):
        """
        Signal connected as HIGH
        """
        self.wire_stim.value = 1
        self.assertTrue(self.wire_stim.value)
        self.assertTrue(self.wire_eval.value)
        self.wire_stim.value = 0  # revert at end of test
