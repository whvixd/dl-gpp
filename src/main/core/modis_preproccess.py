# coding=utf-8
import sys
import agpredict as ap
import os
import subprocess


def start():
    my_args = sys.argv
    print("Running script:", sys.argv[0])
    a = sys.argv[1:]
    print("Arguments passed to script:", my_args)

    directory = '/Users/whvixd/Documents/individual/MODIS/dataset/SL'
    username = 'whvixd'
    password = '1130Wang1130'
    # h21v03,h22v03,h22v04,h23v03,h23v04,h23v05,h24v03,h24v04,h24v05,h24v06,h25v03,h25v04,h25v05,h25v06,h26v03,h26v04,h26v05,h26v06,h27v04,h27v05,h27v06,h28v04,h28v05,h28v06,h28v07,h29v05,h29v06,h30v06

    # china_tiles = ['h21v03','h22v03','h22v04','h23v03','h23v04','h23v05','h24v03','h24v04','h24v05','h24v06','h25v03',
    #                'h25v04','h25v05','h25v06','h26v03','h26v04','h26v05','h26v06','h27v04','h27v05','h27v06','h28v04',
    #                'h28v05','h28v06','h28v07','h29v05','h29v06','h30v06']

    china_tiles = ['h25v08', 'h26v08']
    today = '2021-01-01'
    enddate = '2022-01-01'
    # 让输出成的文件格式以它为标准
    # arcmap创建空间参考图像 https://desktop.arcgis.com/zh-cn/arcmap/latest/tools/data-management-toolbox/create-spatial-reference.htm
    referenceImage = '/Users/whvixd/Documents/individual/MODIS/dataset/SL/SL.tif'
    downloadF = 0

    mod17 = ap.MOD17A2H(directory=directory, username=username, password=password, dataset='MOD17A2H.006',
                        subset='1 0 0',
                        tiles=china_tiles, today=today, enddate=enddate, referenceImage=referenceImage, downloadF=downloadF)

    mod17.pre_process()
    # 批下载
    # mod17.download()
    # 拼接
    # mod17.mosaic()
    # 重投影，转成参考图像格式tif文件
    # mod17.convert()
    mod17.clip()
    # 将所有的{dataset}.npy 保存在一个文件中，finalMatrix.npy
    mod17.finalMatrixFunction()


def start_gpp():
    my_args = sys.argv
    print("Running script:", sys.argv[0])
    print("Arguments passed to script:", my_args)

    directory = '/Users/whvixd/Documents/individual/MODIS/dataset/gpp/china2001'
    username = 'whvixd'
    password = '1130Wang1130'
    # h21v03,h22v03,h22v04,h23v03,h23v04,h23v05,h24v03,h24v04,h24v05,h24v06,h25v03,h25v04,h25v05,h25v06,h26v03,h26v04,h26v05,h26v06,h27v04,h27v05,h27v06,h28v04,h28v05,h28v06,h28v07,h29v05,h29v06,h30v06

    # fixme 用工具下载出现304重定向，然后提示loop，下载失败，后面还是在网页上直接下载吧
    china_tiles = ['h21v03','h22v03','h22v04','h23v03','h23v04','h23v05','h24v03','h24v04','h24v05','h24v06','h25v03',
                   'h25v04','h25v05','h25v06','h26v03','h26v04','h26v05','h26v06','h27v04','h27v05','h27v06','h28v04',
                   'h28v05','h28v06','h28v07','h29v05','h29v06','h30v06']

    today = '2000-01-01'
    enddate = '2001-01-01'
    # 让输出成的文件格式以它为标准
    # arcmap创建空间参考图像 https://desktop.arcgis.com/zh-cn/arcmap/latest/tools/data-management-toolbox/create-spatial-reference.htm
    referenceImage = '/Users/whvixd/Documents/individual/MODIS/dataset/china_5km_referenceImagine.tif' # todo 修改分辨率，由500m->5km
    downloadF = 0

    mod17 = ap.MOD17A2H(directory=directory, username=username, password=password, dataset='MOD17A2H.006',
                        subset='1 0 0',
                        tiles=china_tiles, today=today, enddate=enddate, referenceImage=referenceImage, downloadF=downloadF)


    # 下载数据
    # mod17.download()
    # 将同一时刻的不同tile拼接在一起，生成mos{dataset}_{band}.tif，vrt，xml文件
    mod17.mosaic()
    # 投影 转换成参考图像的坐标投影，生成full{dataset}_{band}.tif，删除mosaic函数生成的文件
    # mod17.convert()
    # 裁剪 成参考图像的大小，full{dataset}_{band}.tif
    # mod17.clip()

if __name__ == '__main__':
    start_gpp()