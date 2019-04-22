import unittest
import upytester
import random
import time

class ReactionTimeTest(unittest.TestCase):
    def setUp(self):
        self.pyb_a = upytester.project.get_device('pyb_a')

    def tearDown(self):
        self.pyb_a.close()

    def test_reaction_time(self):
        """
        Test your reaction time
        """
        time.sleep(2 + random.random() * 5)  # wait random time
        t = self.pyb_a.reaction_time()(timeout=1)
        self.assertIsNotNone(t)
        self.assertLess(t, 300)
