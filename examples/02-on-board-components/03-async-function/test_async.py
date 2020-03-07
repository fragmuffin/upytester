import unittest
import upytester


class ReactionTimeTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.pyb_a = upytester.project.get_device('pyb_a')

    @classmethod
    def tearDownClass(self):
        self.pyb_a.close()

    #def test_blink_func(self):
    #    """Run async function."""
    #    self.pyb_a.async_blink(1)

    def test_blink_remote(self):
        """Create object and run async function."""
        obj = self.pyb_a.Foo(2)
        obj.blink()
