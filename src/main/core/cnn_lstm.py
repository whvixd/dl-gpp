import torch.nn as nn
import numpy as np
import torch.optim
from torch.utils.data import DataLoader, Dataset
import matplotlib.pyplot as plt

from torchvision import transforms

t_list = [i * 0.1 for i in range(0, 100)]
x = [t ** 2 + 10 * t + 0.01 for t in t_list]
x_len = len(x)

# plt.rcParams['figure.figsize'] = (5, 2.5)
# plt.plot(t_list, x)
# plt.xlabel('x')  # x轴名称
# plt.ylabel('(x)')  # y轴名称
# plt.show()




xx = []
for i in range(x_len):
    xx.append(x[i:i + 1])

x_np = np.array(xx, dtype=np.float32)

# 标准化处理，加速收敛
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler(feature_range=(-2, 2))
x_np = scaler.fit_transform(x_np)

from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error


def Evaluate(y_test, y_pre):
    MAPE = 100 * np.mean(np.abs((y_pre - y_test) / y_test))
    MAE = mean_absolute_error(y_test, y_pre)
    R2 = r2_score(y_test, y_pre)
    MSE = mean_squared_error(y_test, y_pre)
    RMSE = np.sqrt(mean_squared_error(y_test, y_pre))
    M = [MAPE, MAE, R2, MSE, RMSE]
    return M

seq = 5
X = []
Y = []

for i in range(x_len - seq):
    X.append(x_np[i:i + seq])
    Y.append(x_np[i + seq:i + seq + 1])


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


split = int(0.7 * x_len)
trainX, trainY = X[:split], Y[:split]


testX, testY = X[split:], Y[split:]
train_dataset = LstmDataset(trainX, trainY)
# 一次向lstm投入6个样本，样本之间没有相关性且随机
train_loader = DataLoader(dataset=train_dataset, batch_size=6, shuffle=True)

test_dataset = LstmDataset(testX, testY)
test_loader = DataLoader(dataset=test_dataset, batch_size=6, shuffle=True)


class LSTM_model(nn.Module):
    def __init__(self, input_size=1, hidden_size=32, output_size=1, num_layers=2):
        super(LSTM_model, self).__init__()

        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.num_layers = num_layers

        self.rnn = nn.LSTM(input_size=self.input_size,
                           hidden_size=self.hidden_size,
                           num_layers=self.num_layers,
                           batch_first=True)

        self.linear = nn.Sequential(
            nn.Linear(self.hidden_size, self.output_size)
        )

    def forward(self, x):
        # x = x.permute(0, 2, 1)
        y, (ht, ct) = self.rnn(x)
        # 一次投入batch数据到lstm中，隐藏层为1,输入xt=[x1,x2,x3,x4]->lstm->返回的是ht=[h1,h2,h3,h4,h5],y=ht
        # 如果是多层ht是各层的隐藏层,y是最后一层的输出结果
        batch_size, seq_len, hidden_size = y.shape
        # if not y.is_contiguous():
        #     y = y.contiguous()
        # y = y.view(-1, hidden_size)
        y.reshape(batch_size * seq_len, hidden_size)
        y = self.linear(y)
        y_seq = y.shape[1]

        # 取最后一步
        y=y[:,y_seq-1:y_seq,:]

        return y


model = LSTM_model()
loss = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

for i in range(200):
    total_loss = 0
    for idx, (data, label) in enumerate(train_loader):
        # data1 = data.squeeze(1)
        pred = model(torch.autograd.Variable(data))
        # label = label.unsqueeze(1)
        l = loss(pred, label)
        optimizer.zero_grad()
        l.backward()
        optimizer.step()
        total_loss += l.item()

    print("epoch:%d,total_loss=%f" % (i, total_loss))


# 评估模型时使用，失效 dropout BN等
model.eval()

# TODO test集没必要归一化处理
print("...test start...")
preds = []
labels = []
for idx, (x, label) in enumerate(test_loader):
    pred = model(x)
    preds.extend(pred.data.squeeze(1).tolist()) # squeeze去掉纬度为1的
    labels.extend(label.squeeze(1).tolist())
print(preds)
print(labels)
print(Evaluate(np.array(labels), np.array(preds)))
