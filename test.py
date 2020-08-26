import unittest
from timeline import TimelineLogic


class TestBuildCmd(unittest.TestCase):
    def testRightPos(self):
        t = TimelineLogic()
        str = t.getCmdPos('w', 'h')
        self.assertEqual('main_w-ovelay_w:main_h-overlay_h', str)

#
# if __name__ == '__main__':
#     unittest.main()
