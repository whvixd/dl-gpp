import unittest
import osgeo.gdal as gdal
import pymodis
import glob
import numpy as np


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

    def test_gdal(self):
        for i in range(gdal.GetDriverCount()):
            print(i, gdal.GetDriver(i).GetDescription())

    def test_pymodis(self):
        self.fullPath = '/Users/whvixd/Documents/individual/MODIS/dataset/SL/spectral/MOD09A1.006'
        self.subset = '1 1 1 1 1 1 1 0 0 0 0 1 0'
        hdflist = sorted(glob.glob(self.fullPath + '/*.hdf'))

        # 缺少 slugify 包
        from pymodis.convertmodis_gdal import createMosaicGDAL
        for i in range(0, len(hdflist), 2):
            ms = createMosaicGDAL(hdfnames=[hdflist[i], hdflist[i + 1]],
                                  subset=self.subset, outformat='GTiff')
            ms.run(str(hdflist[i].split('.h')[0]) + 'mos.tif')
            ms.write_vrt(output=str(hdflist[i].split('.h')[0]), separate=True)
        mosaicCount = len(glob.glob(self.fullPath + '/*mos.tif'))

    def test_write(self):
        self.subset = '1 0 1'
        self.fullPath = "/Users/whvixd/Documents/individual/MODIS/dataset/SL/spectral/MOD09A1.006/test_metadata_MOD09A1.006.txt"
        with open(self.fullPath, 'w') as f:
            f.write(' '.join(["self.%s = %s" % (k, v) for k, v in self.__dict__.items()]))

    def test_read(self):
        self.fullPath = "/Users/whvixd/Documents/individual/MODIS/dataset/SL/spectral/MOD09A1.006/test_metadata_MOD09A1.006.txt"
        with open(self.fullPath) as f:
            meta = f.read()
            s = 'self.subset'
            subsetI = meta.index(s) + len(s + ':  ')
            print(subsetI)
            first_blank_space = meta[subsetI:len(meta)].index(' ')
            subset = str(meta[subsetI:subsetI + first_blank_space])
            print(subset)

    def test_shelve_write(self):
        import shelve
        with shelve.open("./test_shelve") as db:
            db['name'] = '张三'
            db['age'] = 20

    def test_shelve_read(self):
        import shelve
        with shelve.open("./MOD09A1") as db:
            observations = int(str(db.get('observations')))
            print(observations)

    def test_matrix(self):
        import numpy as np
        from osgeo.gdalconst import GA_ReadOnly

        self.fullPath = '/Users/whvixd/Documents/individual/MODIS/dataset/SL/spectral/MOD09A1.006'
        self.subset='1 1 1 1 1 1 1 0 0 0 0 1 0'
        self.rows=4790
        self.columns=5455
        self.observations=4
        dataCount = self.subset.count('1')
        dataNames = sorted(glob.glob(self.fullPath + '/*.tif'))
        dataNames = dataNames[0:dataCount]
        subsetInt = [int(s) for s in self.subset.split() if s.isdigit()]
        # (52258900, 0)
        DC = np.empty(shape=(self.rows * self.columns * self.observations, 0))
        # 52258900
        DCs = np.empty(shape=(self.rows * self.columns * self.observations, subsetInt.count(1)))

        for i in range(dataCount):
            name = str(dataNames[i])
            # 按时间纬度，将同一时间的tif合并数组中
            dataList = sorted(glob.glob(self.fullPath + '/*' + name[-10:-4] + '.tif'))
            bandDC = np.empty((0, 1))
            for b in dataList:
                # (4790,5455)
                data = gdal.Open(str(b), GA_ReadOnly).ReadAsArray()
                # (4790,5455)
                vec = data.reshape((self.rows * self.columns, 1))
                bandDC = np.append(bandDC, vec, axis=0)
            DC = np.append(DC, bandDC, axis=1)

    def test_np(self):
        a=np.array([[1,2],[1,2],[1,2]])
        a[a==2]=3
        print(a)
        b=a[:-1]
        print(b)

    def test_type_convert(self):
        self.rows = 4790
        self.columns = 5455
        self.observations = 4

        obs = (self.observations / 2)
        outArray = np.empty(shape=((int)(self.rows * self.columns * obs), 0))
        print(outArray.shape)

    def test_grid_final(self):
        self.rows = 4790
        self.columns = 5455
        self.observations = 4
        self.subset = '1 1 1 1 1 1 1 0 0 0 0 1 0'

        lag = 150  # a changer?
        grid_r = (int)(self.rows / lag)
        grid_c = (int)(self.columns / lag)
        obs = (int)(self.observations / 2)

        grid_id = (grid_r + 1) * (grid_c + 1)  # max ID number
        idlist = np.arange(1, grid_id + 1).reshape((grid_r + 1, grid_c + 1))

        grid = np.repeat(idlist, lag, axis=0)
        grid = np.repeat(grid, lag, axis=1)

        grid_sized = grid[0:self.rows, 0:self.columns].reshape((1, self.rows, self.columns))
        grid_rep = np.repeat(grid_sized, obs, axis=0)
        grid_final = grid_rep.reshape((obs * self.rows * self.columns, 1))

    def test_tile(self):
        nrow=4790
        ncol=5455
        intervals=2
        uniq_id = np.tile(range(1, nrow * ncol + 1), intervals)
        print(len(uniq_id))

    def test_np_load(self):
        dat = np.load('/Users/whvixd/Documents/individual/MODIS/dataset/SL/spectral/autocorrelationGrid.npy')
        print("Head and tail:", dat[:151], dat[-1:])

    def test_h2o(self):
        import h2o
        load_data_fp='/data/john/srilanka/h2o_data_withMissingS'

        h2o.init(min_mem_size=200, max_mem_size =210)
        # 导入数据
        data = h2o.import_frame(path=load_data_fp)

        test_index = data['training'] != 1
        test = data[test_index]

        # assert test.dim()[0] + train.dim()[0] == d.dim()[0]

    def test_h2o_dl(self):
        import h2o,sys
        load_data_fp = '/Users/whvixd/Documents/individual/MODIS/dataset/SL/spectral/h2o_data_withMissingS'
        load_train_ind_fp = '/Users/whvixd/Documents/individual/MODIS/dataset/SL/spectral/random_split_for_training.csv'
        saving_fp = '/Users/whvixd/Documents/individual/MODIS/dataset/SL/spectral/dlres_meanimputedS.csv'
        predictors = 'B1_lag B2_lag B3_lag B4_lag B5_lag B6_lag B7_lag time_period EVI_lag'

        evals = 45

        # 初始内存大小
        h2o.init(min_mem_size=400, max_mem_size =410)
        # 导入数据
        d = h2o.import_file(path=load_data_fp)
        #######################################################################
        # 标志为枚举类型
        d['time_period'] = d['time_period'].asfactor()
        assert d['time_period'].isfactor()
        d.describe()

        #######################################################################
        train_index = h2o.import_file(path=load_train_ind_fp)
        # fixme train_index 倒入的应该是索引，如：1，2，3
        d['train_index'] = train_index
        train = d[d['train_index']]

        test_index = d['train_index'] != 1
        test = d[test_index]

        assert test.dim()[0] + train.dim()[0] == d.dim()[0]
if __name__ == '__main__':
    unittest.main()
