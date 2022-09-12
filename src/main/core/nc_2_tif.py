# -*- coding: utf-8 -*-
import numpy as np
import netCDF4 as nc
from osgeo import gdal, osr, ogr
import os
import glob
import datetime


def NC_to_tiffs(data, Output_folder,index):
    nc_data_obj = nc.Dataset(data, mode='r', format="netCDF4")
    nc_data_obj.set_auto_mask(False)
    # print(nc_data_obj,type(nc_data_obj)) # 了解NC_DS的数据类型，<class 'netCDF4._netCDF4.Dataset'>
    # print(nc_data_obj.variables) # 了解变量的基本信息
    # print(nc_data_obj)
    Lon = nc_data_obj.variables['longitude'][:]
    Lat = nc_data_obj.variables['latitude'][:]
    GPP=nc_data_obj.variables['GPP']
    u_arr = np.asarray(GPP)  # 这里根据需求输入想要转换的波段名称
    # print('time_1=',time_1.min(),'time_max=',time_1.max())

    # 影像的左上角和右下角坐标
    LonMin, LatMax, LonMax, LatMin = [Lon.min(), Lat.max(), Lon.max(), Lat.min()]

    # 分辨率计算
    N_Lat = len(Lat) # 纬度，上下
    N_Lon = len(Lon) # 经度 ，左右
    Lon_Res = (LonMax - LonMin) / (float(N_Lon) - 1)
    Lat_Res = (LatMax - LatMin) / (float(N_Lat) - 1)

    # dt = nc_data_obj.id
    # 创建.tif文件
    driver = gdal.GetDriverByName('GTiff')
    out_tif_name = Output_folder + '/' + 'GPP_' + index + '.tif'
    out_tif = driver.Create(out_tif_name, N_Lon,N_Lat , 1, gdal.GDT_Float32)

    # 设置影像的显示范围
    # -Lat_Res一定要是-的
    geotransform = (LonMin, Lon_Res, 0, LatMax, 0, -Lat_Res) # 左上角x坐标， 水平分辨率，旋转参数， 左上角y坐标，旋转参数，竖直分辨率
    # geotransform = (LatMax, 1, -Lat_Res,LonMin, Lon_Res, 1) # 左上角x坐标， 水平分辨率，旋转参数， 左上角y坐标，旋转参数，竖直分辨率
    out_tif.SetGeoTransform(geotransform)

    # 获取地理坐标系统信息，用于选取需要的地理坐标系统
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)  # 定义输出的坐标系为"WGS 84"，AUTHORITY["EPSG","4326"]
    out_tif.SetProjection(srs.ExportToWkt())  # 给新建图层赋予投影信息

    # 去除异常值
    u_arr[u_arr[:, :] == -32767] = -9999

    # 数据写出
    out_tif.GetRasterBand(1).WriteArray(u_arr) # *0.001
    out_tif.GetRasterBand(1).SetNoDataValue(-9999)
    out_tif.FlushCache()  # 将数据写入硬盘
    del out_tif  # 注意必须关闭tif文件
    # return nc_data_obj.variables


def main():
    Input_folder = r'/Users/whvixd/Documents/individual/MODIS/dataset/gpp/2018'
    Output_folder = r'/Users/whvixd/Documents/individual/MODIS/dataset/gpp/2018/tifs'

    # 读取所有nc数据
    data_list = glob.glob(Input_folder + '/*.nc')

    for i in range(len(data_list)):
        data = data_list[i]
        NC_to_tiffs(data, Output_folder,str(i))
        print(data + '-----转tif成功')


if __name__ == '__main__':
    main()

