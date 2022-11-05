from osgeo import gdal
import numpy as np
import rioxarray as rxr

def load_img(path):
    dataset = gdal.Open(path)
    num_bands = dataset.RasterCount
    print(num_bands)

    im_width = dataset.RasterXSize
    im_height = dataset.RasterYSize
    im_data = dataset.ReadAsArray(0, 0, im_width, im_height) # 通道数, 长, 宽
    if num_bands==1:
        return im_data
    im_data = im_data.transpose((2, 0, 1))  # 此步保证矩阵为channel_last模式 -> 长, 宽, 通道数
    return im_data

if __name__ == '__main__':
    tif_1=load_img("/Users/whvixd/Documents/individual/MODIS/dataset/gpp/2018/tifs/GPP_1.tif")
    print(tif_1)
    filename = r'/Users/whvixd/Documents/individual/MODIS/dataset/gpp/2018/tifs/GPP_1.tif'
    ds = rxr.open_rasterio(filename)
    lon, lat = np.meshgrid(ds['x'], ds['y'])
    data = ds[0]
