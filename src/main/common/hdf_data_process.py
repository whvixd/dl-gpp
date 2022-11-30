import xarray as xr
import h5netcdf
import gdal

def get_subdataset(file, varnames):
    g = gdal.Open(file)
    subdatasets = g.GetSubDatasets()
    l = []
    for varname in varnames:
        l.extend([s[0] for s in subdatasets if varname in s[0].split(':')[-1]])
    return l

def read_hdf4(file, varnames):
    ld = []
    fname_list = get_subdataset(file, varnames)
    for fname in fname_list:
        myDataset = xr.open_rasterio(fname)
        ld.append(myDataset.to_dataset(name=fname.split(':')[-1]))
    return xr.merge(ld)

def read_hdf():
    gpp_data=xr.open_rasterio("/Users/whvixd/Documents/PycharmProjects/workspace/dl-gpp/dataset/modis/HEGOUT/MOD11A1.A2014226.h18v04.006.2016206155244_HEGOUT.tif")
    print(gpp_data)

if __name__ == '__main__':
    read_hdf()