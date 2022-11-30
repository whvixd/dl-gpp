import glob
import numpy as np
import xarray as xr

from pyproj import CRS


def get_gpp_array():
    Input_folder = r'/Users/whvixd/Documents/individual/MODIS/dataset/gpp/2018'
    data_list = glob.glob(Input_folder + '/*.nc')

    gpp = []
    for data_file in data_list:
        gpp_data = xr.open_dataset(data_file)
        lon_grid25 = np.arange(73.66, 135.05, 0.5)  # 0.05度 5.5km
        lat_grid25 = np.arange(3.86, 53.55, 0.5)

        tm_grid25 = gpp_data.interp(longitude=lon_grid25, latitude=lat_grid25, method='linear')
        # 转置
        tm_grid25_GPP_data = np.transpose(tm_grid25.GPP.data)
        gpp.append(tm_grid25_GPP_data)
    return gpp


if __name__ == '__main__':
    gpp_list = get_gpp_array()
    gpp_np=np.asarray(gpp_list)
    np.save("gpp_np_05.npy",gpp_np)
