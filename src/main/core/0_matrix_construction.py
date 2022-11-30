# coding=utf-8
import sys
import agpredict as ap
import os
import subprocess

my_args = sys.argv
print("Running script:", sys.argv[0])
a = sys.argv[1:]
print("Arguments passed to script:", my_args)
spectral = a[0]
directory = a[1]
username = a[2]
password = a[3]
tiles = a[4].split()
today = a[5]
enddate = a[6]
# 让输出成的文件格式以它为标准
# arcmap创建空间参考图像 https://desktop.arcgis.com/zh-cn/arcmap/latest/tools/data-management-toolbox/create-spatial-reference.htm
referenceImage = a[7]
downloadF = a[8]
# python -u 0_matrix_construction.py 1 /data/emily/SL
# myusername mypassword 'h25v08 h26v08' 2014-01-30 2014-01-01 /data/emily/WF/NDVI_DC/SL.tif
if spectral == '0':
    # https://lpdaac.usgs.gov/products/mod11a2v061/
    mod11 = ap.MOD11A2(directory=directory, username=username, password=password, dataset='MOD11A2.005',
                       subset='1 1 0 0 0 0 0 0 0 0 0 0',
                       tiles=tiles, today=today, enddate=enddate, referenceImage=referenceImage, downloadF=downloadF)

    mod13 = ap.MOD13Q1(directory=directory, username=username, password=password, dataset='MOD13Q1.006',
                       subset='1 1 1 0 0 0 0 0 0 0 0 1',
                       tiles=tiles, today=today, enddate=enddate, referenceImage=referenceImage, downloadF=downloadF)

    mod15 = ap.MOD15A2(directory=directory, username=username, password=password, dataset='MOD15A2.005',
                       subset='1 1 1 0 0 0',
                       tiles=tiles, today=today, enddate=enddate, referenceImage=referenceImage, downloadF=downloadF)

    mod17 = ap.MOD17A2H(directory=directory, username=username, password=password, dataset='MOD17A2H.005',
                        subset='1 1 1 0 0 0 0 0 0 0 0 0',
                        tiles=tiles, today=today, enddate=enddate, referenceImage=referenceImage, downloadF=downloadF)

    # https://www.jianshu.com/p/821c741ff169
    # https://www.cnblogs.com/suoyike1001/p/15244791.html
    mod11.pre_process()
    mod13.pre_process()
    mod15.pre_process()
    mod17.pre_process()
    mod17.finalMatrix()

if spectral == '1':
    if not os.path.exists(directory):
        os.mkdir(directory)
    if not os.path.exists(directory + '/spectral'):
        os.mkdir(directory + '/spectral')

    mod09 = ap.MOD09A1(directory=directory + '/spectral', username=username, password=password, dataset='MOD09A1.006',
                       subset='1 1 1 1 1 1 1 0 0 0 0 1 0',
                       tiles=tiles, today=today, enddate=enddate, referenceImage=referenceImage, downloadF=downloadF)

    mod09.pre_process()
    if os.path.isfile(directory + '/MOD13Q1.006.npy'):
        subprocess.call(['cp', directory + 'MOD13Q1.npy', directory + 'MOD13Q1.txt', directory + '/spectral'])
    else:
        mod13 = ap.MOD13Q1(directory=directory + '/spectral', username=username, password=password,
                           dataset='MOD13Q1.006', subset='1 1 1 0 0 0 0 0 0 0 0 1',
                           tiles=tiles, today=today, enddate=enddate, referenceImage=referenceImage,
                           downloadF=downloadF)
        mod13.pre_process()

    # 合并到一个矩阵中
    mod09.finalMatrixFunction()

# python -u 0_matrix_construction.py 1 /data/emily/SL myusername mypassword 'h25v08 h26v08' 2014-01-30 2014-01-01 /data/emily/WF/NDVI_DC/SL.tif

'''
/Users/whvixd/opt/anaconda3/envs/python37/bin/python -u 0_matrix_construction.py 1 /Users/whvixd/Documents/individual/MODIS/dataset/SL whvixd 1130Wang1130 'h25v08 h26v08' 2022-03-01 2022-03-30 /Users/whvixd/Documents/individual/MODIS/dataset/SL/SL.tif 1
'''
