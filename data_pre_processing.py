import glob
import pymodis
import logger
import os
try:
    import gdal
except ImportError:
    raise 'Python GDAL library not found, please install python-gdal'



def mosaic():
    """
    If more than two tiles are input by the user, this function mosaics the tiles
    together.
    """

    full_path='/Users/didi/Documents/whvixd/personal/studyAI/dataset/modis/MOD17A2H'
    subset = '1 1 1 0 0 0 0 0 0 0 0 0'
    hdflist = sorted(glob.glob(full_path + '/*.hdf'))
    for i in range(0, len(hdflist), 2):
        ms = pymodis.convertmodis_gdal.createMosaicGDAL(hdfnames=[hdflist[i], hdflist[i + 1]],
                                                        subset=subset,outformat='GTiff')
        ms.run(str(hdflist[i].split('.h')[0]) + 'mos.tif')
        ms.write_vrt(output=str(hdflist[i].split('.h')[0]), separate=True)
    mosaicCount = len(glob.glob(full_path + '/*mos.tif'))
    logger.logger('SUCCESS', 'Mosaic complete!  MODIS tiles %s were successfully mosaicked into %d mosaic images.'
                  % (str(10), mosaicCount))


class MOD17A2():

    def __init__(self, directory, username, password, dataset, subset, tiles, today, enddate, referenceImage):
        self.directory = directory
        self.fullPath = directory + '/' + dataset
        self.username = username
        self.password = password
        self.url = "http://e4ftl01.cr.usgs.gov"
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
        self.referenceImage = gdal.Open(referenceImage)
        self.projection = self.referenceImage.GetProjection()
        geotransform = self.referenceImage.GetGeoTransform()
        self.resolution = geotransform[1]
        self.rows = self.referenceImage.RasterYSize
        self.columns = self.referenceImage.RasterXSize
        self.outformat = self.referenceImage.GetDriver().ShortName

        self.scale = [.0001, .0001, 1]
        self.varNames = ['GP', 'PSN', 'Quality']
        self.qualityBand = 2
        self.fillValue = 30000

        def download(self):

            """
    		Download images for specified tiles and time period.

    		:param filelist: lists all of the HDF files downloaded

    		:param observations:  lists the total number of days worth of data downloaded
    			(e.g. 1 year of data = 23 observations).
    			(e.g. 1 year of data = 23 observations).
    		"""

            if not os.path.exists(self.directory):
                os.mkdir(self.directory)
            if not os.path.exists(self.fullPath):
                os.mkdir(self.fullPath)

            dm = pymodis.downmodis.downModis(self.fullPath, self.password, self.username, self.url, self.tiles,
                                             self.path, self.dataset,
                                             self.today, self.enddate, jpg=False, debug=True, timeout=30)
            dm.connect()
            self.filelist = dm.getListDays()
            self.observations = len(dm.getListDays())

            if self.dataset != 'MOD13Q1.005':
                if self.observations % 2 != 0:
                    raise IOError(
                        "The total number of observations through time must be an even number. Please add or remove an observation before or after %s" % str(
                            self.filelist[0]))

            dm.downloadsAllDay()
            logger.logger('SUCCESS',
                       'Downloading is complete!  %d HDF files of %s data for tiles %s were downloaded for the following days:  %s' % (
                       self.observations * len(self.tiles), str(self.dataset), str(self.tiles), str(self.filelist)))

        def mosaic(self):

            """
    		If more than two tiles are input by the user, this function mosaics the tiles
    		together.
    		"""

            if len(self.tiles) > 1:
                hdflist = sorted(glob.glob(self.fullPath + '/*.hdf'))
                for i in range(0, len(hdflist), 2):
                    ms = pymodis.convertmodis_gdal.createMosaicGDAL(hdfnames=[hdflist[i], hdflist[i + 1]],
                                                                    subset=self.subset, outformat='GTiff')
                    ms.run(str(hdflist[i].split('.h')[0]) + 'mos.tif')
                    ms.write_vrt(output=str(hdflist[i].split('.h')[0]), separate=True)
                mosaicCount = len(glob.glob(self.fullPath + '/*mos.tif'))
                logger.logger('SUCCESS',
                           'Mosaic complete!  MODIS tiles %s were successfully mosaicked into %d mosaic images.' % (
                           str(self.tiles), mosaicCount))

    def imageType(self):
        return 'MOD17A2'

