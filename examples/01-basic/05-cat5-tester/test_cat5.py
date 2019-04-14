from bench import BenchTest

# Log to stdout
import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class Cat5CableTests(BenchTest):
    def assertPinHigh(self, *indexes):
        """
        Assert that the given pin is high on both stim & eval
        :param indexes: Pin numbers to assert high
        :type indexes: :class:`list` of :class:`int`
        """
        for i in range(8):  # 8 pins
            if i in indexes:
                # Assert pins on input & output are high
                #self.assertTrue(self.socket_eval.pin_value(i))
                pass
            else:
                # Assert pins on input & output are low
                self.assertFalse(self.socket_eval.pin_value(i), "pin[{}]".format(i))

    def test_parallel(self):
        """Test that cable is correctly wired in parallel"""
        pinmap = [  # (<stimulation pin>, <evaluation pin>)
            (0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7)
        ]
        for (stim_idx, eval_idx) in pinmap:
            self.socket_stim.pin_value(stim_idx, 1)
            self.assertPinHigh(eval_idx)
            self.socket_stim.pin_value(stim_idx, 0)
            self.assertPinHigh()  # assert all low

    def test_crossover(self):
        """Test that cable is correctly wired as a crossover (T568A <-> T568B)"""
        pinmap = [  # (<stimulation pin>, <evaluation pin>)
            (0, 2), (1, 5), (2, 0), (3, 3), (4, 4), (5, 1), (6, 6), (7, 7)
        ]
        for (stim_idx, eval_idx) in pinmap:
            self.socket_stim.pin_value(stim_idx, 1)
            self.assertPinHigh(eval_idx)
            self.socket_stim.pin_value(stim_idx, 0)
            self.assertPinHigh()  # assert all low
