#!/usr/bin/python
# coding=utf-8

# -*- coding: utf-8 -*-
"""
MODIS Download and Processing Tool

Author:  Emily Burchfield <emily.k.burchfield@vanderbilt.edu>

This package downloades user specified MODIS tiles over a period of time,
mosaics the tiles, reprojects the HDF files, and transforms the images 
into a 2D matrix where each row represents a pixel and each column 
represents a point in time.

@author: Emily Burchfield
"""

# 依赖 操作系统中的 gdal 软件，mac需要 brew install gdal
try:
    import osgeo.gdal as gdal
except ImportError:
    try:
        import gdal
    except ImportError:
        raise 'Python GDAL library not found, please install python-gdal'

try:
    import osgeo.osr as osr
except ImportError:
    try:
        import osr
    except ImportError:
        raise 'Python GDAL library not found, please install python-gdal'

try:
    import pymodis
except ImportError:
    try:
        import pymodis
    except ImportError:
        raise 'PyModis library not found, please install pyModis'

import numpy as np
# from gdalconst import *
from osgeo.gdalconst import GA_ReadOnly

gdal.UseExceptions()
import os, sys
import glob
import subprocess
from abc import ABCMeta
import LogUtil

logging = LogUtil.wrapperLogging()
from ShelveHelper import ShelveWrapper


# from __future__ import division

class ModisImageBase(object):
    """Wrapper for MODIS Imageobjects"""

    __metaclass__ = ABCMeta

    def __init__(self, directory, username, password, dataset, subset, tiles, today, enddate, referenceImage, scale,
                 varNames, qualityBand, fillValue, downloadF, dbName):

        """
		:param directory: path to the directory in which all images and matrices
			will be stored.
		
		:param username: username for NASA's EarthData Login (https://urs.earthdata.nasa.gov/)
		
		:param password: password for NASA's EarthData Login (https://urs.earthdata.nasa.gov/)
		
		:param dataset: full name of MODIS dataset (e.g. MOD13Q1.006)
		
		:param subset: subset of data to be taken from the HDF file as a string of
			0 (do not select data) and 1s (select data).  If, for example, you want
			to process only NDVI and the quality mask from the MOD13Q1.006 dataset, 
			subset = '1 0 0 0 0 0 0 0 0 0 0 1'
		
		:param tiles: string of the MODIS tiles to be downloaded, e.g. 'h08v05'.  
			Adjacent tiles should be written as ['h08v04', 'h08v05']
		
		:param today: the most recent date from which to download data
		
		:param startdate: the start date for the data download
		
		:param referenceImage:  the full path for the reference image that is 
			the size and projection desired for the final dataset.  Use the MODIS
			Projection Tool to build this image.
		
		:param scale:  to scale factor for each dataset in HDF to transform raw data 
			into final data values.  Taken from the NASA website.  User does not 
			need to enter.
		
		:param varNames: variable names of each dataset in the HDF.  User does not 
			need to enter.
		
		:param qualityBand:  flag for the quality dataset.  User does not need to enter.
        
        :param filelist: list of the dates in string format ('YYYY.MM.DD') for which tiles were downloaded
        
        :param observations: total number of days for which tiles were downloaded
        
        :param fullPath:  full path to directory for dataset
        
        :param path:  set to MOLT and currently limited to MODIS Terra datasets
        
        :param extent:  path to the shapefile used to define the extent of the final reprojected, mosaicked images
        
        :param projection:  projection information for the referenceImage
        
        :param resolution:  pixel size for the referenceImage
        
        :param rows:  number of rows in the referenceImage
        
        :param cols: number of columns in the referenceImage
        
        :param outFormat: file extension of the reprojected, mosaicked and clipped images (i.e. GTiff for GeoTiff)
        
        :param scale:  scale factor to transform the original HDF data into scaled data (included below, user need not enter)
        
        :param varNames:  names of each of the datasets in the HDF file (included below, user need not enter)
        
        :param qualityBand:  flag for the location of the quality dataset in the original HDF file
        
        
		"""

        self.directory = directory
        self.fullPath = directory + '/' + dataset  ###how else to connect path?
        self.username = username
        self.password = password
        self.url = 'http://e4ftl01.cr.usgs.gov'
        self.path = 'MOLT'
        self.dataset = dataset
        self.subset = subset
        self.tiles = tiles
        if len(self.tiles) > 2:
            raise IOError("A maximum of two MODIS tiles can be included. Please remove extra tiles")
        self.today = today
        self.enddate = enddate

        self.referenceImagePath = referenceImage
        self.extent = self.fullPath + '/referenceExtent.shp'
        self.referenceImage = gdal.Open(referenceImage)
        self.projection = self.referenceImage.GetProjection()
        gt = self.referenceImage.GetGeoTransform()
        self.resolution = gt[1]
        self.rows = self.referenceImage.RasterYSize
        self.columns = self.referenceImage.RasterXSize
        self.outformat = self.referenceImage.GetDriver().ShortName

        self.scale = scale
        self.varNames = varNames
        self.qualityBand = qualityBand
        self.fillValue = fillValue
        # 是否需要下载原数据
        self.downloadF = downloadF == '1'
        self.dbName = dbName

    def fill_args(self, dm):
        self.filelist = dm.getListDays()
        self.observations = len(dm.getListDays())

        db = ShelveWrapper(self.dbName)
        db.insert('filelist', self.filelist)
        db.insert('observations', self.observations)

        if self.dataset != 'MOD13Q1.006':
            if self.observations % 2 != 0:
                raise IOError(
                    "The total number of observations through time must be an even number. Please add or remove an observation before or after %s" % str(
                        self.filelist[0]))

    def download(self):

        """
		Download images for specified tiles and time period.
		
		:param filelist: lists all of the HDF files downloaded
		
		:param observations:  lists the total number of days worth of data downloaded
			(e.g. 1 year of data = 23 observations).
			(e.g. 1 year of data = 23 observations).
		"""

        if self.downloadF is not None and not self.downloadF:
            logging.debug('download return,downloadF is false')
            db = ShelveWrapper(self.dbName)
            self.filelist = db.read('filelist')
            self.observations = int(str(db.read('observations')))
            if self.dataset != 'MOD13Q1.006':
                if self.observations % 2 != 0:
                    raise IOError(
                        "The total number of observations through time must be an even number. Please add or remove an observation before or after %s" % str(
                            self.filelist[0]))
            return

        if not os.path.exists(self.directory):
            os.mkdir(self.directory)
        if not os.path.exists(self.fullPath):
            os.mkdir(self.fullPath)

        logging.debug('downloading is start,dataset:%s' % self.dataset)
        dm = pymodis.downmodis.downModis(self.fullPath, self.password, self.username, self.url, self.tiles, self.path,
                                         self.dataset,
                                         self.today, self.enddate, jpg=False, debug=True, timeout=30)
        dm.connect()

        self.fill_args(dm)

        dm.downloadsAllDay()
        logging.info(
            'Downloading is complete!  %d HDF files of %s data for tiles %s were downloaded for the following days:  %s' % (
                self.observations * len(self.tiles), str(self.dataset), str(self.tiles), str(self.filelist)))

    def mosaic(self):

        """
		If more than two tiles are input by the user, this function mosaics the tiles
		together.		如果用户输入的图像块超过两个，则该函数将这些图像块拼接在一起。
		"""

        logging.debug('Mosaic start! DataSet:%s,tiles:%s .' % (self.dataset, str(self.tiles)))
        if len(self.tiles) > 1:
            # 获取所有的hdf文件
            hdflist = sorted(glob.glob(self.fullPath + '/*.hdf'))

            # i:0,2
            for i in range(0, len(hdflist), 2):
                # 一个使用GDAL将modis数据从hdf格式拼接到GDAL格式的类
                ms = pymodis.convertmodis_gdal.createMosaicGDAL(hdfnames=[hdflist[i], hdflist[i + 1]],
                                                                subset=self.subset, outformat='GTiff')
                ms.run(str(hdflist[i].split('.h')[0]) + 'mos.tif')
                ms.write_vrt(output=str(hdflist[i].split('.h')[0]), separate=True)
            mosaicCount = len(glob.glob(self.fullPath + '/*mos.tif'))

            logging.info(
                'Mosaic complete! DataSet:%s, MODIS tiles %s were successfully mosaicked into %d mosaic images.' % (
                    self.dataset, str(self.tiles), mosaicCount))

    def convert(self):

        """
		This function converts the HDF files into the file extension of the 
		referenceImage.  It projects images into the projection of the referenceImage using the vrt files produced in the mosaic step.  
        If no vrt files were produced in the previous step, it converts the original hdf files.  

		这个函数将HDF文件转换为referenceImage的文件扩展名。它使用拼接步骤中生成的vrt文件将图像投射到referenceImage的投影中。
		如果在上一步中没有生成vrt文件，它将转换原始的hdf文件。
		"""

        logging.debug('Convert start! DataSet:%s,tiles:%s .' % (self.dataset, str(self.tiles)))

        vrtlist = sorted(glob.glob(self.fullPath + '/*vrt'))
        splitAt = len(self.fullPath) + 1

        if len(vrtlist) != 0:
            for i in range(0, len(vrtlist)):
                prefix = str(vrtlist[i].split(".vrt")[0])
                prefix = prefix[:splitAt] + 'full' + prefix[splitAt:]
                ct = pymodis.convertmodis_gdal.convertModisGDAL(hdfname=vrtlist[i],
                                                                prefix=prefix, subset=self.subset, res=self.resolution,
                                                                outformat=self.outformat, wkt=self.projection,
                                                                resampl='NEAREST_NEIGHBOR', vrt=True)
                ct.run()
            mosdel = glob.glob(self.fullPath + '/*mos.tif')
            for f in mosdel:
                os.remove(f)
            xmldel = glob.glob(self.fullPath + '/*mos.tif.xml')
            for f in xmldel:
                os.remove(f)
            vrtdel = glob.glob(self.fullPath + '/*.vrt')
            for f in vrtdel:
                os.remove(f)
            tifCount = len(glob.glob(self.fullPath + '/*.tif'))
            dataCount = self.subset.count('1')

            logging.info(
                'Conversion complete! DataSet:%s, The %d bands of %d mosaicked images were successfully converted to %d %s files.' % (
                    self.dataset, dataCount, len(vrtlist), tifCount, str(self.outformat)))

        if len(vrtlist) == 0:

            hdflist = sorted(glob.glob(self.fullPath + '/*.hdf'))
            for i in range(len(hdflist)):
                ms = pymodis.convertmodis_gdal.createMosaicGDAL(hdfnames=[hdflist[i]], subset=self.subset,
                                                                outformat='GTiff')
                ms.run(str(hdflist[i].split('.h')[0]) + 'mos.tif')
                ms.write_vrt(output=str(hdflist[i].split('.h')[0]), separate=True)

            vrtlist = sorted(glob.glob(self.fullPath + '/*vrt'))
            splitAt = len(self.fullPath) + 1

            for i in range(0, len(vrtlist)):
                prefix = str(vrtlist[i].split(".vrt")[0])
                prefix = prefix[:splitAt] + 'full' + prefix[splitAt:]
                ct = pymodis.convertmodis_gdal.convertModisGDAL(hdfname=vrtlist[i],
                                                                prefix=prefix, subset=self.subset, res=self.resolution,
                                                                outformat=self.outformat, wkt=self.projection,
                                                                resampl='NEAREST_NEIGHBOR', vrt=True)
                ct.run()

            mosdel = glob.glob(self.fullPath + '/*mos.tif')
            for f in mosdel:
                os.remove(f)
            xmldel = glob.glob(self.fullPath + '/*mos.tif.xml')
            for f in xmldel:
                os.remove(f)
            vrtdel = glob.glob(self.fullPath + '/*.vrt')
            for f in vrtdel:
                os.remove(f)
            tifCount = len(glob.glob(self.fullPath + '/full*.tif'))
            dataCount = self.subset.count('1')

            logging.info(
                'Conversion complete! DataSet:%s, The %d bands of %d HDF files were successfully converted to %d %s files.' % (
                    self.dataset, dataCount, len(hdflist), tifCount, str(self.outformat)))

    def clip(self):

        """
		This function clips the mosaicked, projected images to the size of the
		referenceImage

		这个函数将拼接的投影图像剪辑到referenceImage的大小
		"""
        # 此程序生成一个shapefile，其中包含每个输入栅格文件的记录、包含文件名的属性以及概述栅格的多边形几何图形。此输出适用于 MapServer 作为栅格tileindex。

        logging.debug('Clip start! DataSet:%s,tiles:%s .' % (self.dataset, str(self.tiles)))

        subprocess.call(['gdaltindex', self.extent, self.referenceImagePath])
        dataNames = sorted(glob.glob(self.fullPath + '/full*.tif'))
        splitAt = len(self.fullPath) + 1

        for i in range(len(dataNames)):
            x = dataNames[i]
            y = dataNames[i][:splitAt] + dataNames[i][splitAt + 4:]
            # 这个 gdalwarp 实用程序是一种图像拼接、重投影和扭曲实用程序。该程序可以重新投影到任何支持的投影，也可以应用与图像一起存储的gcp，如果图像是带有控制信息的“原始”图像。
            subprocess.call(
                ['gdalwarp', '-r', 'near', '-cutline', self.extent, '-crop_to_cutline', x, y, '-dstnodata', '9999'])

        for n in dataNames:
            os.remove(n)
        dataNames = sorted(glob.glob(self.fullPath + '/*.tif'))
        test = gdal.Open(dataNames[0]).ReadAsArray()

        logging.info(
            'Clipping complete! DataSet:%s, %d %s files  were successfully clipped to the size of %s with dimensions %d rows by %d columns' % (
                self.dataset, len(dataNames), str(self.outformat), str(self.referenceImagePath), test.shape[0],
                test.shape[1]))

    def matrix(self):

        """
		This function transforms the images into a single numpy array with dimensions
		pixels by observations.  If the image has 100 pixels for 1 year (23 observations)
		then this matrix should have dimensions 100 rows by 23 columns.  The matrix
		includes the quality mask dataset.  This matrix is not yet masked for quality control.

		这个函数将图像转换为一个单一的数字数组，尺寸像素通过观察。如果图像有100像素为1年(23个观察)，那么这个矩阵应该有尺寸100行23列。
		该矩阵包括质量掩码数据集。为了进行质量控制，这个矩阵还没有被掩盖。
		"""

        logging.debug('Matrix start! DataSet:%s,tiles:%s .' % (self.dataset, str(self.tiles)))
        dataCount = self.subset.count('1')
        dataNames = sorted(glob.glob(self.fullPath + '/*.tif'))
        dataNames = dataNames[0:dataCount]
        subsetInt = [int(s) for s in self.subset.split() if s.isdigit()]

        DC = np.empty(shape=(self.rows * self.columns * self.observations, 0))
        DCs = np.empty(shape=(self.rows * self.columns * self.observations, subsetInt.count(1)))

        logging.debug('combining data start, DataSet:%s,rows:%d,columns:%d,observations:%d,count(subset==1):%d' %
                      (self.dataset, self.rows, self.columns, self.observations, subsetInt.count(1)))
        # 数据类型
        for i in range(dataCount):
            name = str(dataNames[i])
            # 原来是两个步长，我现在用半个月的数据，这里的dataList.size()是等于observations
            # 按时间纬度，将同一时间的tif合并数组中
            dataList = sorted(glob.glob(self.fullPath + '/*' + name[-10:-4] + '.tif'))
            bandDC = np.empty((0, 1))
            for b in dataList:
                data = gdal.Open(str(b), GA_ReadOnly).ReadAsArray()
                vec = data.reshape((self.rows * self.columns, 1))
                bandDC = np.append(bandDC, vec, axis=0)
            DC = np.append(DC, bandDC, axis=1)
            del vec, bandDC, data
            logging.debug('combining data complete, DataSet:%s,dataName:%s,dataList:%s,DC.shape:%s' %
                          (self.dataset, name, dataList, str(DC.shape)))

        logging.debug('apply fill values,DataSet:%s,fillValue:%s' %
                      (self.dataset, str(self.fillValue)))

        # apply fill values
        if self.dataset == 'MOD15A2.005' or self.dataset == 'MOD17A2.005':
            DC[DC > self.fillValue] = 9999.0
        if self.dataset == 'MOD11A2.005':
            DC[:, 0][DC[:, 0] == self.fillValue] = 9999.0  # this should have fixed it!
        else:
            # 将9999.0替换fillValue
            DC[DC == self.fillValue] = 9999.0

            # scale dataset
        count = 0
        for i in range(len(subsetInt)):
            if subsetInt[i] == 1:
                DCs[:, count] = np.multiply(DC[:, count], self.scale[i])
                count += 1
        # ???
        DCs[DC == 9999.0] = 9999.0
        self.DC = DCs
        del DC

        # 将对象属性输入到本地中
        # metadata function，fixme 保存数据确实，DC数组过大，一些数据省略了
        with open(self.fullPath + '/' + 'metadata_' + self.dataset + '.txt', 'w') as f:
            f.write(' '.join(["self.%s = %s" % (k, v) for k, v in self.__dict__.items()]))

        logging.info(
            'DataSet:%s.The %s data was transformed into an array with dimensions %d rows by %d columns.  No data value set to 9999. '
            ' A metadata file with object attributes was created.  To access the matrix, simply call object.DC' % (
                self.dataset, str(self.outformat), self.DC.shape[0], self.DC.shape[1]))

        tif = sorted(glob.glob(self.fullPath + '/*.tif'))
        for t in tif:
            os.remove(t)

    def quality(self):

        """
        This function applies the MODIS quality mask to the dataset.  
        Masked pixels are given a value of 9999.0.
        该函数将MODIS质量掩码应用于数据集。蒙面像素的值为9999.0。
        """

        logging.debug('Quality start! DataSet:%s,tiles:%s .' % (self.dataset, str(self.tiles)))
        subsetInt = [int(s) for s in self.subset.split() if s.isdigit()]
        columnNames = []
        for i in range(len(subsetInt)):
            if subsetInt[i] == 1:
                columnNames.append(self.varNames[i])

        # qualityBand number of subset
        q = columnNames.index('Quality')

        if subsetInt[self.qualityBand] == 1:
            dataCount = self.subset.count('1')
            QC = np.repeat(self.DC[:, q].reshape((self.DC.shape[0], 1)), dataCount - 1, axis=1)
            if self.dataset == 'MOD09A1.006' or self.dataset == 'MOD13Q1.006':
                QC = np.uint16(QC)
            else:
                QC = np.uint8(QC)

            QCm = QC & 1  # flips DCm mask
            DCm = np.delete(self.DC, q, 1)  # looks good

            DCm = np.ma.masked_where(QCm == 1, DCm)
            DCm = np.ma.masked_where(DCm == 9999.0, DCm)

            obs: int = 0
            if len(self.tiles) > 1:
                obs = (int)(self.observations / len(self.tiles))
            if len(self.tiles) == 1:
                obs = (int)(self.observations / 2)

            outArray = np.empty(shape=((int)(self.rows * self.columns * obs), 0))
            for b in range(0, self.DC.shape[1] - 1):
                cfull = DCm[:, b].reshape((self.observations, self.rows, self.columns))
                b16 = np.empty(shape=(self.rows * self.columns * obs, 0))
                for band in range(0, cfull.shape[0], 2):
                    c16 = np.ma.mean(cfull[band:band + 1, :, :], axis=0)
                    c16f = np.ma.filled(c16, 9999.0).astype(float).reshape((self.rows * self.columns))
                    b16 = np.append(b16, c16f)
                outArray = np.append(outArray, b16.reshape((obs * self.rows * self.columns, 1)), axis=1)

            self.finalDC = outArray

            np.save(str(self.directory) + '/' + self.dataset + '.npy', self.finalDC)
            del outArray, QC, DCm

            outfile = str(self.directory) + '/' + self.dataset + '.txt'
            f = open(outfile, 'w')
            for name in columnNames:
                if name != 'Quality':
                    f.write(name + '\n')
            var = [a for a in columnNames if not a.startswith('Quality')]

            logging.info(
                'DataSet:%s.The final 16-day interval quality-masked matrix was created successfully.  This matrix has dimensions %d rows by %d columns.  Datasets included in the matrix are %s' % (
                    self.dataset, self.finalDC.shape[0], self.finalDC.shape[1], var))

        if subsetInt[self.qualityBand] != 1:
            cleanDC = np.delete(self.DC, q, 1)

            obs: int = 0
            if len(self.tiles) > 1:
                obs = (int)(self.observations / len(self.tiles))
            if len(self.tiles) == 1:
                obs = (int)(self.observations / 2)

            outArray = np.empty(shape=((int)(self.rows * self.columns * obs), 0))
            for b in range(cleanDC.shape[1]):
                cfull = cleanDC[:, b].reshape((self.observations, self.rows, self.columns))
                b16 = np.empty(shape=(self.rows * self.columns * obs))
                for band in range(cfull.shape[0]):
                    c16 = np.mean(cfull[band:band + 1, :, :], axis=0)
                    band16 = np.append(b16, c16, axis=0)
                outArray = np.append(outArray, b16.reshape((obs * self.rows * self.columns, 1)), axis=1)

            np.save(self.directory + '/' + self.dataset + '.npy', self.finalDC)
            del cleanDC, outArray

            outfile = self.directory + '/' + self.dataset + '.txt'
            f = open(outfile, 'w')
            for name in columnNames:
                if name != 'Quality':
                    f.write(str(name) + ' \n')
            var = [a for a in columnNames if not a.startswith('Quality')]

            logging.info(
                'DataSet:%s.The final 16-day interval matrix was created successfully.  A quality mask was not applied, though remaining no data values are set at 9999.  This matrix has dimensions %d rows by %d columns.  Datasets included in the matrix are %s' % (
                    self.dataset, self.finalDC.shape[0], self.finalDC.shape[1], var))

    def qualityCheck(self):
        logging.debug('QualityCheck start! DataSet:%s,tiles:%s .' % (self.dataset, str(self.tiles)))
        d = self.fullPath
        dataset = self.dataset

        outfile = d + '/qualityCheck' + dataset + '.txt'
        sys.stdout = open(outfile, 'w')

        array = np.load(d + '.npy')
        t = d + '.txt'
        with open(t, 'r') as tfile:
            text = tfile.read().split('\n')
        text = text[0:-1]
        nv = array.max()

        # entire dataset
        print('Data for entire array of %s data:' % (dataset))
        print('\t>>> included datasets: %s' % (str(text)))
        print('\t>>> shape:', array.shape)
        print('\t>>> max w nv:', array.max())
        print('\t>>> max wo nv:', array[array < nv].max())
        print('\t>>> min wo nv:', array[array < nv].min())
        print('\t>>> mean wo nv:', array[array < nv].mean())

        # each band
        for b in range(array.shape[1]):
            print('Data for column %d, %s:' % (b, text[b]))
            print('\t>>> max w nv:', array[:, b].max())
            print('\t>>> max wo nv:', array[:, b][array[:, b] < nv].max())
            print('\t>>> min wo nv:', array[:, b][array[:, b] < nv].min())
            print('\t>>> mean wo nv:', array[:, b][array[:, b] < nv].mean())

        sys.stdout = sys.__stdout__

        logging.info(
            'QualityCheck complete,DataSet:%s.See file qualityCheck%s.txt for detailed information about the final matrix.' % (
                self.dataset, self.dataset))

    def prepare(self):
        # 下载数据
        self.download()
        # 拼接
        # self.mosaic()
        # 投影 转换成参考图像的扩展名
        # self.convert()
        # 裁剪 成参考图像的大小
        # self.clip()
        # 转成矩阵
        # self.matrix()
        # self.quality()
        # self.qualityCheck()

    def finalMatrixFunction(self):
        logging.debug('FinalMatrixFunction start! DataSet:%s,tiles:%s .' % (self.dataset, str(self.tiles)))
        obs: int = 0
        if len(self.tiles) > 1:
            obs = (int)(self.observations / len(self.tiles))
        if len(self.tiles) == 1:
            obs = (int)(self.observations / 2)

        # 添加经纬度的列
        # create latitude/longitude grid
        xoff, a, b, yoff, d, e = self.referenceImage.GetGeoTransform()

        def pixel2coord(x, y):
            xp = a * x + b * y + xoff
            yp = d * x + e * y + yoff
            return (xp, yp)

        arr = self.referenceImage.ReadAsArray()
        lat = np.empty(shape=(arr.shape[0], arr.shape[1]))
        lon = np.empty(shape=(arr.shape[0], arr.shape[1]))

        for row in range(arr.shape[0]):
            for col in range(arr.shape[1]):
                coor = pixel2coord(row, col)
                lat[row, col] = coor[0]
                lon[row, col] = coor[1]

        grid_rep = np.repeat(lat.reshape((1, lat.shape[0], lat.shape[1])), obs, axis=0)
        lat = grid_rep.reshape((grid_rep.shape[1] * grid_rep.shape[0] * grid_rep.shape[2], 1))

        grid_repl = np.repeat(lon.reshape((1, lon.shape[0], lon.shape[1])), obs, axis=0)
        lon = grid_repl.reshape((grid_repl.shape[1] * grid_repl.shape[0] * grid_repl.shape[2], 1))

        np.save(str(self.directory) + '/' + 'latitude.npy', lat)
        np.save(str(self.directory) + '/' + 'longitude.npy', lon)

        latfile = str(self.directory) + '/latitude.txt'
        f = open(latfile, 'w')
        f.write('latitude \n')
        f.close()
        lonfile = str(self.directory) + '/longitude.txt'
        l = open(lonfile, 'w')
        l.write('longitude \n')
        l.close()

        logging.info(
            'FinalMatrixFunction process,DataSet:%s,Latitude and longitude arrays successfully created minimum latitude %d and minimum longitude %d' %
            (self.dataset, lat.min(), lon.min()))
        del lat, lon

        # 添加时间纬度的列
        # time array
        x = np.repeat(np.array(range(1, obs + 1)), self.rows * self.columns)
        time = np.reshape(x, (self.rows * self.columns * obs, 1))

        np.save(str(self.directory) + '/' + 'time.npy', time)
        timefile = str(self.directory) + '/time.txt'
        t = open(timefile, 'w')
        t.write('timeID \n')
        t.close()

        logging.debug(
            'FinalMatrixFunction process,DataSet:%s.Time ID created with maximum time value of %d and dimensions of %d rows by %d columns' %
            (self.dataset, time.max(), time.shape[0], time.shape[1]))
        del x, time

        # 150的含义是？？？
        # autocorrelation
        lag = 150  # a changer?
        grid_r = (int)(self.rows / lag)
        grid_c = (int)(self.columns / lag)
        rem_r = self.rows % lag
        rem_c = self.columns % lag

        grid_id = (grid_r + 1) * (grid_c + 1)  # max ID number
        idlist = np.arange(1, grid_id + 1).reshape((grid_r + 1, grid_c + 1))

        grid = np.repeat(idlist, lag, axis=0)
        grid = np.repeat(grid, lag, axis=1)

        grid_sized = grid[0:self.rows, 0:self.columns].reshape((1, self.rows, self.columns))
        grid_rep = np.repeat(grid_sized, obs, axis=0)
        grid_final = grid_rep.reshape((obs * self.rows * self.columns, 1))

        np.save(str(self.directory) + '/' + 'autocorrelationGrid.npy', grid_final)
        autofile = str(self.directory) + '/autocorrelationGrid.txt'
        a = open(autofile, 'w')
        a.write('autocorrelationGrid' + ' ' + '\n')
        a.close()
        logging.info(
            'FinalMatrixFunction process,DataSet:%s.Autocorrelation grid created with pixel lag of %d and dimensions of %d rows by %d columns' %
            (self.dataset, lag, grid_final.shape[0], grid_final.shape[1]))
        del idlist, grid_sized, grid

        # append txt file
        out = str(self.directory) + '/columnNames.txt'
        columnNames = sorted(glob.glob(self.directory + '/*.txt'))

        with open(out, 'w') as outfile:
            for fname in columnNames:
                with open(fname) as infile:
                    outfile.write(infile.read())

        # 将 光谱纬度的数据合并到一个数组中 autocorrelationGrid.npy、MOD09A1.006.npy、MOD13Q1.006.npy
        matrixNames = sorted(glob.glob(self.directory + '/*.npy'))
        matrix = np.empty(shape=(self.rows * self.columns * obs, 0))

        for i in range(len(matrixNames)):
            c = np.load(matrixNames[i])
            if len(c.shape) == 1:
                c = c.reshape((self.rows * self.columns * obs, 1))
            else:
                c = c.reshape((self.rows * self.columns * obs, c.shape[1]))
            matrix = np.append(matrix, c, axis=1)

        vn = open(out)
        var = vn.read()

        self.finalMatrix = matrix

        np.save(str(self.directory) + '/finalMatrix.npy', matrix)
        logging.info(
            'FinalMatrixFunction process,DataSet:%s.Final matrix created as finalMatrix.npy in %s. Column names for the matrix can be foud in columnNames.txt.  To access matrix, call object.finalDC' %
            (self.dataset, str(self.directory)))
        logging.info(
            'FinalMatrixFunction process,DataSet:%s.Final matrix with size of %d rows by %d columns.  To access matrix, call object.finalMatrix.  The matrix includes the following variables: %s' %
            (self.dataset, matrix.shape[0], matrix.shape[1], str(var)))

    @staticmethod
    def imageType():
        pass


class MOD09A1(ModisImageBase):

    def __init__(self, directory, username, password, dataset, subset, tiles, today, enddate, referenceImage,
                 downloadF):
        scale = [.0001, .0001, .0001, .0001, .0001, .0001, .0001, 1, .01, .01, .01, 1, 1]
        varNames = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'Quality 32', 'Solar Zenith', 'View Zenith',
                    'Relative Azimuth', 'Quality', 'DOY']
        qualityBand = 11
        fillValue = -28672
        # 是否需要再下载数据
        dbName = MOD09A1.imageType()
        super().__init__(directory, username, password, dataset, subset, tiles, today, enddate, referenceImage, scale,
                         varNames, qualityBand, fillValue, downloadF, dbName)

    @staticmethod
    def imageType():
        return 'MOD09A1'


class MOD13Q1(ModisImageBase):

    def __init__(self, directory, username, password, dataset, subset, tiles, today, enddate, referenceImage,
                 downloadF):

        scale = [.0001, .0001, 1, .0001, .0001, .0001, .0001, .01, .01, .1, 1, 1]
        varNames = ['NDVI', 'EVI', 'Quality', 'Red', 'NIR', 'Blue', 'MIR', 'View Zenith', 'Sun Zenith', 'Azimuth',
                    'DOY', 'Pixel Reliability']
        qualityBand = 2
        fillValue = -3000
        dbName = MOD13Q1.imageType()

        super().__init__(directory, username, password, dataset, subset, tiles, today, enddate, referenceImage, scale,
                         varNames, qualityBand, fillValue, downloadF, dbName)

    def prepare(self):
        # 下载数据
        self.download()
        # 拼接
        self.mosaic()
        # 投影 转换成参考图像的扩展名
        self.convert()
        # 裁剪 成参考图像的大小
        self.clip()
        # 转成矩阵
        self.matrix()
        self.quality()
        self.qualityCheck()

    def quality(self):

        subsetInt = [int(s) for s in self.subset.split() if s.isdigit()]

        # varnames file
        columnNames = []
        for i in range(len(subsetInt)):
            if subsetInt[i] == 1:
                columnNames.append(self.varNames[i])

        q = columnNames.index('Quality')

        if subsetInt[self.qualityBand] == 1:
            dataCount = self.subset.count('1')
            QC = np.repeat(self.DC[:, q].reshape((self.DC.shape[0], 1)), dataCount - 1, axis=1)
            QC = np.uint16(QC)
            QCm = QC & 1
            DCm = np.delete(self.DC, q, 1)
            DCm = np.ma.masked_where(QCm == 1, DCm)
            outArray = np.ma.filled(DCm, 9999.0)
            outArray.astype(float)
            self.finalDC = outArray

            np.save(str(self.directory) + '/' + self.dataset + '.npy', self.finalDC)
            outfile = str(self.directory) + '/' + self.dataset + '.txt'
            f = open(outfile, 'w')
            for name in columnNames:
                if name != 'Quality':
                    f.write(name + ' ' + '\n')
            f.close()
            var = [a for a in columnNames if not a.startswith('Quality')]
            logging.info(
                'The final 16-day interval quality-masked matrix was created successfully.  This matrix has dimensions %d rows by %d columns.  Datasets included in the matrix are %s' % (
                    self.finalDC.shape[0], self.finalDC.shape[1], str(var)))

        if subsetInt[self.qualityBand] != 1:
            self.finalDC = np.delete(self.DC, q, 1)
            np.save(str(self.directory) + '/' + str(self.dataset) + '.npy', self.finalDC)
            outfile = str(self.directory) + '/' + str(self.dataset) + '.txt'
            f = open(outfile, 'w')
            for name in columnNames:
                if name != 'Quality':
                    f.write(name + ' ' + '\n')
            f.close()
            var = [a for a in columnNames if not a.startswith('Quality')]
            logging.info(
                'The final 16-day interval matrix was created successfully.  A quality mask was not applied, though no data values are set at 9999.  This matrix has dimensions %d rows by %d columns.  Datasets included in the matrix are %s.  To access the final matrix, call object.finalDC' % (
                    self.finalDC.shape[0], self.finalDC.shape[1], str(var)))

    def finalMatrixFunction(self):
        logging.debug('FinalMatrixFunction start! DataSet:%s,tiles:%s .' % (self.dataset, str(self.tiles)))
        # create latitude/longitude grid
        global obs
        xoff, a, b, yoff, d, e = self.referenceImage.GetGeoTransform()

        def pixel2coord(x, y):
            xp = a * x + b * y + xoff
            yp = d * x + e * y + yoff
            return (xp, yp)

        arr = self.referenceImage.ReadAsArray()
        lat = np.empty(shape=(arr.shape[0], arr.shape[1]))
        lon = np.empty(shape=(arr.shape[0], arr.shape[1]))

        # 遍历矩阵（二位数组）
        for row in range(arr.shape[0]):
            for col in range(arr.shape[1]):
                coor = pixel2coord(row, col)
                lat[row, col] = coor[0]
                lon[row, col] = coor[1]

        lat = np.repeat(lat.reshape((arr.shape[0] * arr.shape[1], 1)), self.observations)
        lon = np.repeat(lon.reshape((arr.shape[0] * arr.shape[1], 1)), self.observations)

        np.save(str(self.directory) + '/' + 'latitude.npy', lat)
        np.save(str(self.directory) + '/' + 'longitude.npy', lon)

        latfile = str(self.directory) + '/latitude.txt'
        f = open(latfile, 'w')
        f.write('latitude' + ' ' + '\n')
        f.close()
        lonfile = str(self.directory) + '/longitude.txt'
        l = open(lonfile, 'w')
        l.write('longitude' + ' ' + '\n')
        l.close()

        logging.info(
            'Latitude and longitude arrays successfully created  with minimum latitude %d and minimum longitude %d' % (
                lat.min(), lon.min()))

        del lat, lon

        # time
        x = np.repeat(np.array(range(1, self.observations + 1)), self.rows * self.columns)
        time = np.reshape(x, (self.rows * self.columns * self.observations, 1))

        np.save(str(self.directory) + '/' + 'time.npy', time)
        timefile = str(self.directory) + '/time.txt'
        t = open(timefile, 'w')
        t.write('timeID' + ' ' + '\n')
        t.close()
        logging.info(
            'Time ID created with maximum time value of %d and dimensions of %d rows by %d columns' % (
                time.max(), time.shape[0], time.shape[1]))

        del x, time

        # autocorrelation
        lag = 150  # a changer?
        grid_r = self.rows / lag
        grid_c = self.columns / lag
        rem_r = self.rows % lag
        rem_c = self.columns % lag

        grid_id = (grid_r + 1) * (grid_c + 1)  # max ID number
        idlist = np.arange(1, grid_id + 1).reshape((grid_r + 1, grid_c + 1))

        grid = np.repeat(idlist, lag, axis=0)
        grid = np.repeat(grid, lag, axis=1)

        grid_sized = grid[0:self.rows, 0:self.columns].reshape((1, self.rows, self.columns))
        grid_rep = np.repeat(grid_sized, obs, axis=0)
        grid_final = grid_rep.reshape((obs * self.rows * self.columns, 1))

        np.save(str(self.directory) + '/' + 'autocorrelationGrid.npy', grid_final)
        autofile = str(self.directory) + '/autocorrelationGrid.txt'
        a = open(autofile, 'w')
        a.write('autocorrelationGrid' + ' ' + '\n')
        a.close()
        logging.info(
            'Autocorrelation grid created with pixel lag of %d and dimensions of %d rows by %d columns' % (
                lag, grid_final.shape[0], grid_final.shape[1]))
        del idlist, grid_sized, grid

        # append txt file
        out = str(self.directory) + '/columnNames.txt'
        columnNames = sorted(glob.glob(self.directory + '/*.txt'))

        with open(out, 'w') as outfile:
            for fname in columnNames:
                with open(fname) as infile:
                    outfile.write(infile.read())

        matrixNames = sorted(glob.glob(self.directory + '/*.npy'))
        matrix = np.empty(shape=(self.rows * self.columns * self.observations, 0))  # make sure inherits observations

        for i in range(len(matrixNames)):
            c = np.load(matrixNames[i])
            if len(c.shape) == 1:
                c = c.reshape((self.rows * self.columns * self.observations, 1))
            else:
                c = c.reshape((self.rows * self.columns * self.observations, c.shape[1]))
            matrix = np.append(matrix, c, axis=1)

        vn = open(out)
        vn = vn.read()

        np.save(str(self.directory) + '/finalMatrix.npy', matrix)
        logging.info(
            'Final matrix created as finalMatrix.npy in %s. Column names for the matrix can be foud in columnNames.txt.' % (
                self.directory))
        logging.info(
            'Final matrix with size of %d rows by %d columns.  Matrix includes the following variables: %s' % (
                matrix.shape[0], matrix.shape[1], str(vn)))

    @staticmethod
    def imageType():
        return 'MOD13Q1'


class MOD11A2(ModisImageBase):

    def __init__(self, directory, username, password, dataset, subset, tiles, today, enddate, referenceImage,
                 downloadF):
        scale = [.02, 1, .1, 1, .02, 1, .1, 1, .002, .002, 1, 1]  # plus -65 and .49 on LPDAAC?
        # https://lpdaac.usgs.gov/products/mod11a2v061/
        varNames = ['LST', 'Quality', 'Day View Time', 'Day View Angle', 'LST NIght', 'QC Night',
                    'Night View Time', 'Night View Angle', 'Band 31', 'Band 32', 'Clear Sky Days',
                    'Clear Sky Nights']
        qualityBand = 1
        fillValue = 0
        # 是否需要再下载数据

        dbName = MOD11A2.imageType()
        super().__init__(directory, username, password, dataset, subset, tiles, today, enddate, referenceImage, scale,
                         varNames, qualityBand, fillValue, downloadF, dbName)

    @staticmethod
    def imageType():
        return 'MOD11A2'


class MOD15A2(ModisImageBase):

    def __init__(self, directory, username, password, dataset, subset, tiles, today, enddate, referenceImage,
                 downloadF):
        scale = [1, .01, .1, 1, .01, .1]  ##
        varNames = ['Quality', 'FPAR', 'LAI', 'Extra QC', 'FPAR SD', 'LAI SD']
        qualityBand = 0  ###
        fillValue = 248
        # 是否需要再下载数据

        dbName = MOD11A2.imageType()

        super().__init__(directory, username, password, dataset, subset, tiles, today, enddate, referenceImage, scale,
                         varNames, qualityBand, fillValue, downloadF, dbName)

    @staticmethod
    def imageType():
        return 'MOD15A2'


class MOD17A2(ModisImageBase):

    def __init__(self, directory, username, password, dataset, subset, tiles, today, enddate, referenceImage,
                 downloadF):
        scale = [.0001, .0001, 1]
        varNames = ['GP', 'PSN', 'Quality']
        qualityBand = 2
        fillValue = 30000
        # 是否需要再下载数据

        dbName = MOD11A2.imageType()

        super().__init__(directory, username, password, dataset, subset, tiles, today, enddate, referenceImage, scale,
                         varNames, qualityBand, fillValue, downloadF, dbName)

    @staticmethod
    def imageType():
        return 'MOD17A2'
