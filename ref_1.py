# coding=utf-8
import numpy as np
import os
import pyhdf.SD as hdf
import Image
import scipy as sp
import osgeo.gdal as gdal
import osgeo.osr as osr
from osgeo.gdalconst import *
import re

# 定义文件输入和输出路径
path = 'D:/GJSF/DATA/2908'
# path='D:/GJSF/DATA/jx'
savepth = 'D://GJSF//DATA//TIFF'

# 从影像中得到数据集
lista = os.listdir(path)
datalist = []
for k in range(len(lista)):
    strpth = path + '/' + lista[k]
    dt = hdf.SD(strpth)
    dataset = dt.select('Percent_Tree_Cover')
    data = dataset.get()
    # 将所有的数据暂时存入一个列表中
    datalist.append(data)

# 进行数据叠加处理
dtarelist = []
for m in range(len(datalist)):
    dtarelist.append((datalist[m].reshape((1, 4800, 4800))))

for a in range(len(datalist)):
    if a == 0:
        dtaz = np.concatenate([dtarelist[a], dtarelist[a + 1]], axis=0)
    if a > 1:
        dtaz = np.concatenate([dtaz, dtarelist[a]], axis=0)

# 清理内存空间
del (dataset)
del (data)
del (datalist)
del (dtarelist)

# 数据分割处理


# dtalist=[]
# dtalist.append(dtaz[0:11,0:2400,0:2400])
# dtalist.append(dtaz[0:11,0:2400,2400:4800])
# dtalist.append(dtaz[0:11,2400:4800,0:2400])
# dtalist.append(dtaz[0:11,2400:4800,2400:4800])


# del(dtaz)
# 采用最小二乘法，实现线性拟合，并得到斜率值
# 设定时间数组
Arraytime = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
Time = np.vstack([Arraytime, np.ones(len(Arraytime))]).T
# 定义结果存储数组
temparray = []

XL = np.zeros((4800, 4800), dtype=np.float)
# 进行斜率值的计算

for r in range(4800):
    for c in range(4800):
        for k in range(11):
            temparray.append(dtaz[k, r, c])
        Arrayslope = np.array(temparray)
        temparray = []
        m, b = np.linalg.lstsq(Time, Arrayslope)[0]
        XL[r, c] = m

# 将结果输出为tiff影像
driver = gdal.GetDriverByName("GTiff")
driver.Register()
print
np.max(XL)
tifsavepth = savepth + '/' + '2908.tif'
outDataset = driver.Create(tifsavepth, 4800, 4800, 1, gdal.GDT_Float32)
# 定义空间参考坐标系
proj = osr.SpatialReference()
proj.ImportFromProj4("+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs")
outDataset.SetProjection(proj.ExportToWkt())

sd = hdf.SD('D:/GJSF/DATA/2908/MOD44B.A2000065.h29v08.005.2011259234325.hdf')
md = sd.attributes()['StructMetadata.0'][0:1111]
mu = re.search("UpperLeftPointMtrs=(.+)", md)
UpperLeftPointMtrs = md[mu.start():mu.end()]
x0, y0 = eval(UpperLeftPointMtrs[19:])
mu = re.search("LowerRightMtrs=(.+)", md)
LowerRightMtrs = md[mu.start():mu.end()]
x1, y1 = eval(LowerRightMtrs[15:])

geotransform = (x0, (x1 - x0) / 4800, 0, y0, 0, -(y1 - y0) / 4800)
outDataset.SetGeoTransform(geotransform)

band = outDataset.GetRasterBand(1)
dataset = band.WriteArray(XL)