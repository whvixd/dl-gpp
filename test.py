import unittest
from topng import *

class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

    def test_tif2png(self):
        # MOD11A1.A2014226.mosaic_QC_Day_vrt MOD11A1.A2014226.mosaic_QC_Night_vrt.tif 这两张图渲染图片有问题
        # gdaldem color-relief -of PNG /Users/didi/PycharmProjects/dl-gpp/sources/modis/MOD11A1.A2014226.mosaic_QC_Night_vrt.tif /Users/didi/PycharmProjects/dl-gpp/colortable_58792 /Users/didi/PycharmProjects/dl-gpp/sources/modis/MOD11A1.A2014226.mosaic_QC_Night_vrt_temp.png
        tif2png("/Users/didi/PycharmProjects/dl-gpp/sources/modis/MOD11A1.A2014226.mosaic_QC_Day_vrt.tif")
        self.assertEqual(True, True)  # add assertion here


if __name__ == '__main__':
    unittest.main()
