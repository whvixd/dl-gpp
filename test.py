import unittest
from topng import *
import sys
import agpredict as ap
import os
import subprocess

class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

    def test_tif2png(self):
        # MOD11A1.A2014226.mosaic_QC_Day_vrt MOD11A1.A2014226.mosaic_QC_Night_vrt.tif 这两张图渲染图片有问题
        # gdaldem color-relief -of PNG /Users/didi/PycharmProjects/dl-gpp/sources/modis/MOD11A1.A2014226.mosaic_QC_Night_vrt.tif /Users/didi/PycharmProjects/dl-gpp/colortable_58792 /Users/didi/PycharmProjects/dl-gpp/sources/modis/MOD11A1.A2014226.mosaic_QC_Night_vrt_temp.png
        tif2png("/Users/didi/PycharmProjects/dl-gpp/sources/modis/MOD11A1.A2014226.mosaic_QC_Day_vrt.tif")
        self.assertEqual(True, True)  # add assertion here

    def test_something1(self):
        directory= '/tmp/whvixd/SL'
        username= 'whvixd'
        password= '1130Wang1130'
        tiles='h25v08'.split()
        today='2014-01-30'
        enddate='2014-01-01'
        referenceImage='/tmp/whvixd/WF/NDVI_DC/SL.tif'
        if not os.path.exists(directory):
            os.mkdir(directory)
        if not os.path.exists(directory + '/spectral'):
            os.mkdir(directory + '/spectral')
        mod09 = ap.MOD09A1(directory=directory + '/spectral', username=username, password=password,
                           dataset='MOD09A1.006',
                           subset='1 1 1 1 1 1 1 0 0 0 0 1 0',
                           tiles=tiles, today=today, enddate=enddate, referenceImage=referenceImage)

        mod09.prepare()
        if os.path.isfile(directory + '/MOD13Q1.006.npy'):
            subprocess.call(['cp', directory + 'MOD13Q1.npy', directory + 'MOD13Q1.txt', directory + '/spectral'])
        else:
            mod13 = ap.MOD13Q1(directory=directory + '/spectral', username=username, password=password,
                               dataset='MOD13Q1.006', subset='1 0 1 0 0 0 0 0 0 0 0 1',
                               tiles=tiles, today=today, enddate=enddate, referenceImage=referenceImage)
            mod13.prepare()

        # 矩阵化，图片->矩阵
        mod09.finalMatrix()


if __name__ == '__main__':
    unittest.main()
