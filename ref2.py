import os
import glob
from IPython.core.display import Image
from pymodis import downmodis
from topng import hdf2png

# ##############下载##############
dest = "./sources/modis"

# self._getUsedLayers() 获取层级，1：需要，0：不需要提取
subset = [1, 1, 0, 0, 1, 1]
def downloan():
    # destination foldert

    # tiles to download （下载的区域）
    tiles = "h18v04,h19v04"
    # starting day
    day = "2014-08-14"
    # number of day to download
    delta = 1

    # modisDown = downmodis.downModis(destinationFolder=dest, tiles=tiles, today=day, delta=delta,
    #                             user='whvixd',password='1130Wang1130')
    # print("downmodis.downModis")
    # modisDown.connect()
    # print("downmodis.connect")
    # modisDown.downloadsAllDay()
    # print("modisDown.downloadsAllDay")

    # create the list of files to use
    files = glob.glob(os.path.join(dest, 'MOD11A1.A2014*.hdf'))
    print(files)

    pngfile = hdf2png(files[0])
    Image(filename=pngfile)
    return files


# ##############解析##############
def parse(files):
    # We import the needed modules and after we obtain a list with the full path to the downloaded MODIS files
    from pymodis import parsemodis

    # Parse single data
    # At this point we can parse one file (in this case the first one), creating a parseModis object
    # 解析MOD11A1.A2014226.h18v04.006.2016206155244.hdf.xml 元数据信息
    modisParse = parsemodis.parseModis(files[0])

    # Now you can obtain several parameters from the MODIS metadata, we query only some values to show you:
    # bounding box of the tiles
    # 获取文件的元数据，该方法获取经纬度的min和max
    modisParse.retBoundary()

    # quality statistics
    # 获取 MeasuredParameter 信息
    modisParse.retMeasure()

    # 获取时间范围参数
    modisParse.retRangeTime()

    # jupyter notebook 中的?是文档, ! 用于执行操作系统的命令
    # parsemodis.parseModis?

    # After the test with only a MODIS file, we are going to test the parsing for multiple files
    modisMultiParse = parsemodis.parseModisMulti(files)

    # Now you can obtain the value of boundary
    modisMultiParse.valBound()
    modisMultiParse.boundary

    # or write a xml for a MODIS mosaic file
    modisMultiParse.writexml(os.path.join(dest, 'modismultiparse.xml'))

    f = open(os.path.join(dest, 'modismultiparse.xml'))
    lines = f.readlines()
    p = [l.strip() for l in lines]
    f.close()
    # at the end you can read the created file and print the lines
    print("\n".join(p))

def mosaic(files):
    from pymodis.convertmodis_gdal import createMosaicGDAL
    # [daily temp, quality for daily, not used, not used, nightly temp, quality for nightly]

    output_pref = os.path.join(dest, 'MOD11A1.A2014226.mosaic')
    output_tif = os.path.join(dest, 'MOD11A1.A2014226.mosaic.tif')

# First we'll initialize the mosaic object
    # the first parameter is a list with the original tiles,
    # the second one is a list with the the subset to process,
    # the last is the output format, in this case GeoTiff
    mosaic = createMosaicGDAL(files, subset, 'GTiff')

# At this point we create the xml file with the information of input data,
# and a multilayr GeoTiff file containing the mosaic of the choosen band
    mosaic.run(output_tif)

# Finally we can also create a GDAL VRT(Virtual World) file, a XML file containing the information about input data.
# This is really powerfull if you want convert it in different format or projection system
    mosaic.write_vrt(output_pref)

def convert(files):
    # In this first example we are going to convert an original MODIS HDF file using GDAL library
    from pymodis.convertmodis_gdal import convertModisGDAL
    output_pref = os.path.join(dest, 'MOD11A1.A2014226.h18v04')

    # We are going to convert a single tile, with the 'subset' already used for mosaicking, the output resolution
    # will be 1000 meters and the projection system will be EU-LAEA
    convertsingle = convertModisGDAL(hdfname=files[0], prefix=output_pref, subset=subset, res=1000, epsg=3035)
    convertsingle.run()

# VRT mosaic file
    # We created separated VRT file, one for each choosen subset. So first we collect the name of VRT files
    vrtfiles = glob.glob(os.path.join(dest, 'MOD11A1.A2014*.vrt'))
    print("vrtfiles",vrtfiles)

    # Now we can convert all the VRT files in a for loop
    for f in vrtfiles:
        base = os.path.basename(f).replace('.vrt', '_vrt')
        output = os.path.join(dest, base)
        convertsingle = convertModisGDAL(hdfname=f, prefix=output, subset=[1, 1, 1, 1], res=1000, epsg=3035, vrt=True)
        convertsingle.run_vrt_separated()

        # It will create 4 GeoTIFF files ready to be processed.
        vrttiffiles = glob.glob(os.path.join(dest, 'MOD11A1.A2014*_vrt.tif'))
        print("vrttiffiles:",vrttiffiles)

        from topng import tif2png
        pngfile = tif2png(vrttiffiles[0])
        Image(filename=pngfile)

if __name__ == '__main__':
    files=downloan()
    # parse(files)
    mosaic(files)
    # convert(files)
    from osgeo import gdal


    # dst_ds = None
    # src_ds = None
