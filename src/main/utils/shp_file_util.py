# -*- coding: utf-8 -*-
try:
    from osgeo import gdal
    from osgeo import ogr
    from osgeo import osr
except ImportError:
    import gdal
    import ogr
    import osr


# 写入shp文件,polygon
def writeShp():
    # 支持中文路径
    gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "YES")
    # 属性表字段支持中文
    gdal.SetConfigOption("SHAPE_ENCODING", "UTF-8")
    # 注册驱动
    ogr.RegisterAll()
    # 创建shp数据
    strDriverName = "ESRI Shapefile"
    oDriver = ogr.GetDriverByName(strDriverName)
    if oDriver == None:
        return "驱动不可用：" + strDriverName
    # 创建数据源
    oDS = oDriver.CreateDataSource("polygon.shp")
    if oDS == None:
        return "创建文件失败：polygon.shp"
    # 创建一个多边形图层，指定坐标系为WGS84
    papszLCO = []
    geosrs = osr.SpatialReference()
    geosrs.SetWellKnownGeogCS("WGS84")
    # 线：ogr_type = ogr.wkbLineString
    # 点：ogr_type = ogr.wkbPoint
    ogr_type = ogr.wkbPolygon
    # 面的类型为Polygon，线的类型为Polyline，点的类型为Point
    oLayer = oDS.CreateLayer("Polygon", geosrs, ogr_type, papszLCO)
    if oLayer == None:
        return "图层创建失败！"
    # 创建属性表
    # 创建id字段
    oId = ogr.FieldDefn("id", ogr.OFTInteger)
    oLayer.CreateField(oId, 1)
    # 创建name字段
    oName = ogr.FieldDefn("name", ogr.OFTString)
    oLayer.CreateField(oName, 1)
    oDefn = oLayer.GetLayerDefn()
    # 创建要素
    # 数据集
    # wkt_geom id name
    features = ['test0;POLYGON((-1.58 0.53, -0.79 0.55, -0.79 -0.23, -1.57 -0.25, -1.58 0.53))',
                'test1;POLYGON((-1.58 0.53, -0.79 0.55, -0.79 -0.23, -1.57 -0.25, -1.58 0.53))']
    for index, f in enumerate(features):
        oFeaturePolygon = ogr.Feature(oDefn)
        oFeaturePolygon.SetField("id", index)
        oFeaturePolygon.SetField("name", f.split(";")[0])
        geomPolygon = ogr.CreateGeometryFromWkt(f.split(";")[1])
        oFeaturePolygon.SetGeometry(geomPolygon)
        oLayer.CreateFeature(oFeaturePolygon)
    # 创建完成后，关闭进程
    oDS.Destroy()
    return "数据集创建完成！"


# 读shp文件
def readShp():
    # 支持中文路径
    gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "YES")
    # 支持中文编码
    gdal.SetConfigOption("SHAPE_ENCODING", "UTF-8")
    # 注册所有的驱动
    ogr.RegisterAll()
    # 打开数据
    ds = ogr.Open("polygon.shp", 0)
    if ds == None:
        return "打开文件失败！"
    # 获取数据源中的图层个数，shp数据图层只有一个，gdb、dxf会有多个
    iLayerCount = ds.GetLayerCount()
    print("图层个数 = ", iLayerCount)
    # 获取第一个图层
    oLayer = ds.GetLayerByIndex(0)
    if oLayer == None:
        return "获取图层失败！"
    # 对图层进行初始化
    oLayer.ResetReading()
    # 输出图层中的要素个数
    num = oLayer.GetFeatureCount(0)
    print("要素个数 = ", num)
    result_list = []
    # 获取要素
    for i in range(0, num):
        ofeature = oLayer.GetFeature(i)
        id = ofeature.GetFieldAsString("id")
        name = ofeature.GetFieldAsString('name')
        geom = str(ofeature.GetGeometryRef())
        result_list.append([id, name, geom])
    ds.Destroy()
    del ds
    return result_list


# 读shp文件
def readShpExt():
    # 支持中文路径
    gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "YES")
    # 支持中文编码
    gdal.SetConfigOption("SHAPE_ENCODING", "UTF-8")
    # 注册所有的驱动
    ogr.RegisterAll()
    # 打开数据
    ds = ogr.Open("/Users/whvixd/Documents/individual/MODIS/dataset/SL/MOD17A2H.006/referenceExtent.shp", 0)
    if ds == None:
        return "打开文件失败！"
    # 获取数据源中的图层个数，shp数据图层只有一个，gdb、dxf会有多个
    iLayerCount = ds.GetLayerCount()
    print("图层个数 = ", iLayerCount)
    # 获取第一个图层
    oLayer = ds.GetLayerByIndex(0)
    if oLayer == None:
        return "获取图层失败！"
    # 对图层进行初始化
    oLayer.ResetReading()
    # 输出图层中的要素个数
    num = oLayer.GetFeatureCount(0)
    print("要素个数 = ", num)
    result_list = []
    # 获取要素
    for i in range(0, num):
        ofeature = oLayer.GetFeature(i)
        location = ofeature.GetFieldAsString("location")
        # name = ofeature.GetFieldAsString('name')
        geom = str(ofeature.GetGeometryRef())
        result_list.append([location, geom])
    ds.Destroy()
    del ds
    return result_list


if __name__ == '__main__':
    # writeResult = writeShp()
    # print(writeResult)
    # readResult = readShp()
    # print(readResult)

    print(readShpExt())