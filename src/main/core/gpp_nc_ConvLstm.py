# -*- coding: utf-8 -*-
import numpy as np
import netCDF4 as nc
import torchvision.transforms
from osgeo import gdal, osr, ogr
import os
import glob
import convolution_lstm
import datetime
import torch.nn as nn
import torch
import convolution_lstm_ex2
from torch.utils.data import DataLoader, Dataset


def getGPP(data):
    nc_data_obj = nc.Dataset(data, mode='r', format="netCDF4")
    nc_data_obj.set_auto_mask(False)
    GPP = nc_data_obj.variables['GPP']
    u_arr = np.asarray(GPP)  # 这里根据需求输入想要转换的波段名称
    return u_arr


def main():
    Input_folder = r'/Users/whvixd/Documents/individual/MODIS/dataset/gpp/2018'

    # 读取所有nc数据
    data_list = glob.glob(Input_folder + '/*.nc')

    gpp_arr = []
    for i in range(len(data_list)):
        data = data_list[i]
        gpp_data = getGPP(data)
        data = []
        data.append(gpp_data)
        gpp_arr.append(data)

    x_len = len(gpp_arr)
    seq = 3
    X = []
    Y = []

    for i in range(x_len - seq):
        X.append(gpp_arr[i:i + seq])
        Y.append(gpp_arr[i + seq:i + seq + 1])

    # 耗时
    trainX = torch.tensor(X,dtype=torch.float32)
    trainY = torch.tensor(Y,dtype=torch.float32)
    train_dataset = LstmDataset(trainX, trainY)
    train_loader = DataLoader(dataset=train_dataset, batch_size=1, shuffle=True)

    # model = convolution_lstm.ConvLSTM(input_channels=1, hidden_channels=[16,8, 4, 2], kernel_size=3)

    model=convolution_lstm_ex2.ConvLSTM(input_dim=1, hidden_dim=8, kernel_size=(3, 3), num_layers=2,
             batch_first=True, bias=True, return_all_layers=False)

    loss = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    for i in range(10):
        total_loss = 0
        for idx, (data, label) in enumerate(train_loader):
            # data1 = data.squeeze(1)
            print("input.shape",data.size())
            # 耗时，吃内存
            pred = model(torch.autograd.Variable(data))
            # label = label.unsqueeze(1)
            l = loss(pred, label)
            optimizer.zero_grad()
            l.backward()
            optimizer.step()
            total_loss += l.item()

        print("epoch:%d,total_loss=%f" % (i, total_loss))


class LstmDataset(Dataset):

    def __init__(self, xx, yy, transform=None):
        self.x = xx
        self.y = yy
        self.transform = transform

    def __getitem__(self, index):
        x1 = self.x[index]
        y1 = self.y[index]
        if self.transform != None:
            return self.transform(x1), y1
        return x1, y1

    def __len__(self):
        return len(self.x)


if __name__ == '__main__':
    main()
