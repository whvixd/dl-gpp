import unittest
from data_pre_processing import *


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

    def test_mosaic(self):
        mosaic()
        directory='/Users/didi/Documents/whvixd/personal/studyAI/dataset/modis/MOD17A2H'
        username='whvixd'
        password='Xiang1130*'
        tiles='h25v08 h26v08'
        today='2021-01-30'
        enddate='2021-01-01'
        mod17=MOD17A2(directory=directory, username=username, password=password, dataset='MOD17A2.005',
                       subset='1 1 1 0 0 0 0 0 0 0 0 0',
                       tiles=tiles, today=today, enddate=enddate, referenceImage=referenceImage)

        self.assertEqual(True, True)  # add assertion here


if __name__ == '__main__':
    unittest.main()
