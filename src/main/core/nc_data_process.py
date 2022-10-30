import netCDF4 as nc
import numpy as np
import pandas as pd
import glob


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


if __name__ == '__main__':
    Input_folder = r'/Users/whvixd/Documents/individual/MODIS/dataset/gpp/2018'
    # 读取所有nc数据
    data_list = glob.glob(Input_folder + '/*.nc')
    FILEPATH = data_list[0]
    cut_2_china(FILEPATH)
