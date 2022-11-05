import netCDF4 as nc
import numpy as np
import pandas as pd
import glob
import xarray as xr


def cut_2_china(nc_file_path):
    FILE = nc.Dataset(nc_file_path)
    GPP = FILE['GPP']
    GPP.set_auto_maskandscale(False)
    longitude = np.array(FILE.variables['longitude'][:])
    latitude = np.array(FILE.variables['latitude'][:])
    # scaling_factor = float(str(GPP.scaling_factor))
    # GPP = np.array(GPP[:],dtype=np.float)
    GPP = np.array(GPP[:])

    china_long_index = np.asarray(np.where((73.66 <= longitude) & (longitude <= 135.05)))[0]
    china_lat_index = np.asarray(np.where((3.86 <= latitude) & (latitude <= 53.55)))[0]

    china_long = longitude[china_long_index[0]:china_long_index[-1]]
    china_lat = latitude[china_lat_index[0]:china_lat_index[-1]]
    china_gpp = GPP[china_long_index[0]:china_long_index[-1],
                china_lat_index[0]:china_lat_index[-1]]
    # china_gpp[china_gpp==-9999]=np.nan
    # china_gpp=china_gpp*scaling_factor
    return china_long,china_lat,china_gpp


def summary():
    Input_folder = r'/Users/whvixd/Documents/individual/MODIS/dataset/gpp/2018'

    # 读取所有nc数据
    data_list = glob.glob(Input_folder + '/*.nc')

    FILEPATH = data_list[0]
    FILE = nc.Dataset(FILEPATH)

    # print(FILE)

    # print(FILE.variables)

    GPP = FILE['GPP']
    # print(GPP)
    # print(GPP.shape)
    # print(GPP[3600][1800])

    GPP.set_auto_maskandscale(False)  # 设置缩放和掩膜数组开启，默认就是开启，这句话可省略

    # for key in FILE.variables.keys():
    #     print('{:<5}'.format(key), end=' data shape is : ')
    #     print(FILE.variables[key][:].shape)

    # 填充值处理
    for key in FILE.variables.keys():
        a = FILE[key]
        if hasattr(a, '_FillValue'):
            print('{:<5} has filled value, which is {}'.format(key, a._FillValue), end=', ')
            print('the number of filled value is {}'.format(np.isnan(np.array(FILE.variables[key][:])).sum()))
        else:
            print('{:<5} doesn\'t has filled value'.format(key))

    longitude = np.array(FILE.variables['longitude'][:])
    latitude = np.array(FILE.variables['latitude'][:])

    print("全球经度：", longitude.shape)
    print("全球纬度：", latitude.shape)

    longitude = longitude[73.66 <= longitude]
    china_lon = longitude[longitude <= 135.05]
    latitude = latitude[3.86 <= latitude]
    china_lat = latitude[latitude <= 53.55]

    print("中国经度：", china_lon.shape)
    print("中国纬度：", china_lat.shape)

    # 经度处理
    lon_data = pd.DataFrame({'value': longitude})
    # 经度分为 10 个区间
    quartiles = pd.cut(lon_data.value, 10, precision=0)

    lon_grouped = lon_data.value.groupby(quartiles)

    def get_status(group):
        return {'distribution : ': group.count()}

    print('longitude distribution is : ')
    print(lon_grouped.apply(get_status).unstack())

    # 数据的分布区间
    lat_data = pd.DataFrame({'value': latitude})
    quartiles = pd.cut(lat_data.value, 10, precision=0)

    lat_grouped = lat_data.value.groupby(quartiles)
    print('latitude distribution is : ')
    print(lat_grouped.apply(get_status).unstack())

    GPP_arr = np.array(GPP[:], dtype=np.float)
    GPP_flatten = GPP_arr.flatten()
    GPP_flatten[GPP_flatten == 9999] = np.nan
    print('The number of GPP is {}'.format(len(GPP_flatten)))
    GPP_data = pd.DataFrame({'value': GPP_flatten})
    quartiles = pd.cut(GPP_data.value, 30, precision=0)
    sst_grouped = GPP_data.value.groupby(quartiles)
    print('gpp data distribution is : ')
    print(sst_grouped.apply(get_status).unstack())

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cmaps
import matplotlib as mpl
import matplotlib.pyplot as plt
from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter
import rioxarray as rxr
import shapely
# from osgeo import gdal
# 参考：https://blog.csdn.net/HMXNX/article/details/125281017
def draw_tif():
    def cm2inch(value):
        return value / 2.54

    size1 = 10.5
    fontdict = {'weight': 'bold', 'size': size1, 'color': 'k', 'family': 'SimHei'}
    mpl.rcParams.update(
        {
            'text.usetex': False,
            'font.family': 'stixgeneral',
            'mathtext.fontset': 'stix',
            "font.family": 'serif',
            "font.size": size1,
            "mathtext.fontset": 'stix',
            "font.serif": ['Times New Roman'],
        }
    )

    proj = ccrs.PlateCarree()
    fig, ax = plt.subplots(1, 1, figsize=(cm2inch(16), cm2inch(9)), dpi=100, subplot_kw={'projection': proj})
    # extent = [-180, 180, -90, 90]
    extent = [70, 140, 0, 60]

    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=0.5, zorder=2, color='k')  # 添加海岸线
    ax.add_feature(cfeature.LAND)  # 添加陆地

    # ax.set_xticks(np.arange(extent[0], extent[1] + 1, 60), crs=proj)
    # ax.set_yticks(np.arange(extent[-2], extent[-1] + 1, 30), crs=proj)

    ax.set_xticks(np.arange(extent[0], extent[1] + 1, 0.05), crs=proj)
    ax.set_yticks(np.arange(extent[-2], extent[-1] + 1, 0.05), crs=proj)

    ax.xaxis.set_major_formatter(LongitudeFormatter(zero_direction_label=False))
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.xaxis.set_major_formatter(LongitudeFormatter(zero_direction_label=False))
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.minorticks_on()

    # fixme 没有经纬度数据！
    # filename = r'/Users/whvixd/Documents/individual/MODIS/dataset/gpp/2018/tifs/GPP_1.tif'
    # ds = rxr.open_rasterio(filename)
    #
    # lon, lat = np.meshgrid(ds['x'], ds['y'])
    # data = ds.data

    input_data = r'/Users/whvixd/Documents/individual/MODIS/dataset/gpp/2018/NIRv.GPP.201801.v1.nc'  # 数据存放路径
    gpp_data = xr.open_dataset(input_data)
    # fixme 这里的度数与地图中的不一致
    lon_grid25 = np.arange(73.66, 135.05, 0.05)  # 0.05度 5.5km
    lat_grid25 = np.arange(3.86, 53.55, 0.05)
    # lon_grid25 = np.arange(73.66, 135.05, 1)
    # lat_grid25 = np.arange(3.86, 53.55, 1)

    tm_grid25 = gpp_data.interp(longitude=lon_grid25, latitude=lat_grid25, method='linear')


    lev = np.arange(0, 51, 5)
    # 转置
    tm_grid25_GPP_data=np.transpose(tm_grid25.GPP.data)
    cf = ax.contourf(lon_grid25,lat_grid25, tm_grid25_GPP_data, levels=lev, extend='neither', transform=ccrs.PlateCarree(), cmap=cmaps.rainbow)

    plt.subplots_adjust(right=0.86)
    ax2 = fig.add_axes([0.875, 0.17, 0.02, 0.654])
    b = plt.colorbar(cf, shrink=0.93, orientation='vertical', extend='both', pad=0.035, aspect=30, ticks=lev, cax=ax2)
    b.ax.set_ylabel(r'冠层高度/$\mathrm{m}$', fontdict=fontdict)

    plt.savefig('/Users/whvixd/Documents/individual/MODIS/dataset/gpp/2018/tifs/Figure/GFHD2005.png', dpi=600)
    plt.show()
# shapely和cartopy中pyproj 版本冲突
from shapely.geos import lgeos
if __name__ == '__main__':
    # Input_folder = r'/Users/whvixd/Documents/individual/MODIS/dataset/gpp/2018'
    # # 读取所有nc数据
    # data_list = glob.glob(Input_folder + '/*.nc')
    # FILEPATH = data_list[0]
    # _,_,china_gpp=cut_2_china(FILEPATH)
    # print(china_gpp.shape)

    # filename = r'/Users/whvixd/Documents/individual/MODIS/dataset/gpp/2018/tifs/GPP_1.tif'
    # dataset = gdal.Open(filename)
    # im_width = dataset.RasterXSize
    # im_height = dataset.RasterYSize
    # lon, lat = np.meshgrid(ds['x'], ds['y'])
    # data = ds[0]
    draw_tif()
