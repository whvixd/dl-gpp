from __future__ import division
import csv, time, sys, pickle, h2o
# Hyperopt：是进行超参数优化的一个类库。有了它我们就可以拜托手动调参的烦恼，并且往往能够在相对较短的时间内获取原优于手动调参的最终结果。
from hyperopt import fmin, tpe, hp, STATUS_OK, STATUS_FAIL, Trials
import LogUtil
logging=LogUtil.wrapperLogging()
# from hyperopt import hp

'''
/Users/whvixd/opt/anaconda3/envs/python37/bin/python -u 3_h2o_deeplearning.py 
/Users/whvixd/Documents/individual/MODIS/dataset/SL/spectral/h2o_data_withMissingS 
/Users/whvixd/Documents/individual/MODIS/dataset/SL/spectral/random_split_for_training.csv 
/Users/whvixd/Documents/individual/MODIS/dataset/SL/spectral/dlres_meanimputedS.csv 
B1_lag B2_lag B3_lag B4_lag B5_lag B6_lag B7_lag time_period EVI_lag
'''

my_args = sys.argv
logging.debug("Running script:%s"% sys.argv[0])
my_args = sys.argv[1:]
logging.debug("Arguments passed to script:%s"% my_args)
load_data_fp = my_args[0]
load_train_ind_fp = my_args[1]
saving_fp = my_args[2]
predictors = my_args[3:]

# GWP_lag LST_lag NDVI_lag FPAR_lag LAI_lag GP_lag PSN_lag nino34_lag time_period EVI_lag
# if SPECTRAL B1_lag B2_lag B3_lag B4_lag B5_lag B6_lag B7_lag GWP_lag nino34_lag time_period EVI_lag

evals = 45

logging.debug("Loading in data...")
# 初始内存大小
h2o.init(min_mem_size_GB = 3, max_mem_size_GB = 4)
# 导入数据
d = h2o.import_file(path = load_data_fp)
#######################################################################
# 标志为枚举类型
logging.debug("Making 'time_period' and 'landuse' a factor...")
d['time_period'] = d['time_period'].asfactor()
assert d['time_period'].isfactor()
# logging.debug(d.levels(col='time_period'))

'''
d['landuse'] = d['landuse'].asfactor()
assert d['landuse'].isfactor()
logging.debug(d.levels(col='landuse'))
'''
d.describe()

#######################################################################
train_index = h2o.import_file(path = load_train_ind_fp)
d['train_index'] = train_index
train = d[d['train_index']]

test_index = d['train_index'] != 1 #？？？？
# fixme d[index] 是索引到列
test = d[test_index]

logging.debug("test.dim()[0]:%s,train.dim()[0]:%s,d.dim()[0]:%s"%(test.dim()[0],train.dim()[0],d.dim()[0]))
assert test.dim()[0] + train.dim()[0] == d.dim()[0]
logging.debug("Training data has %d columns and %d rows, test has %d rows."%(train.ncol(), train.nrow(), test.nrow()))

logging.debug("Making data 25% smaller so this doesnt take as long by randomly keeping 75% of the rows.")
r = train[0].runif() # Random UNIform numbers (0,1), one per row
train = train[ r < 0.75 ]
logging.debug("Training data now has %d rows."% train.nrow())

h2o.remove([test_index, train_index, d])
del test_index, train_index, d

def split_fit_predict_dl(h1, h2, h3, hdr1, hdr2, hdr3, rho, epsilon):
    logging.debug("Trying h1, h2, h3, hdr1, hdr2, hdr3, rho, epsilon values of:%s,%s,%s,%s,%s,%s,%s,%s"%
                  (h1, h2, h3, hdr1, hdr2, hdr3, rho, epsilon))
    # H2O是一个基于java的机器学习/深度学习平台，它支持大量无监督和有监督的模型，也支持深度学习算法；可以作为R或Python包导入，也给用户提供UI似的界面
    # from h2o.estimators.deeplearning import H2ODeepLearningEstimator
    dl = h2o.deeplearning(
        # 特征
        x=train[predictors],
        # 标签
        y=train['EVI'],
        validation_x=test[predictors],
        validation_y=test['EVI'],
        training_frame=train,
        validation_frame=test,
        # 权重
        weights_column='PixelReliability',
        # 隐藏层
        hidden=[int(h1), int(h2), int(h3)],
        # 激活函数
        activation="RectifierWithDropout",
        # 隐藏层丢弃率
        hidden_dropout_ratios=[hdr1, hdr2, hdr3],
        fast_mode=True,
        rho=rho,
        epsilon=epsilon)
    # dl.train()
    # 损失函数：均方差
    mse = dl.mse(valid=True)
    r2 = dl.r2(valid=True)
    logging.debug("Deep learning MSE:%s"% mse)
    return ([mse, r2])


def start_save(csvfile, initialize=None):
    if initialize is None:
        initialize = ['mse', 'r2', 'h1', 'h2', 'h3', 'hdr1', 'hdr2',
                      'hdr3', 'rho', 'epsilon', 'timing', 'datetime']
    with open(csvfile, "w") as output:
        writer = csv.writer(output, lineterminator='\n')
        writer.writerow(initialize)


def objective(args):
    h1, h2, h3, hdr1, hdr2, hdr3, rho, epsilon = args
    time1 = time.time()
    try:
        mse, r2 = split_fit_predict_dl(h1, h2, h3, hdr1, hdr2, hdr3, rho, epsilon)
    except:
        logging.debug("Error in trying to fit and then predict with dl model:%s" % sys.exc_info()[0])
        mse = None
        r2 = None
        status = STATUS_FAIL
    else:
        status = STATUS_OK

    timing = time.time() - time1
    datetime = time.strftime("%c")
    tosave = [mse, r2, int(h1), int(h2), int(h3), hdr1, hdr2, hdr3, rho, epsilon, timing, datetime]
    with open(saving_fp, "a") as output:
        writer = csv.writer(output, lineterminator='\n')
        writer.writerow(tosave)
    return {'loss': mse,
            'status': status,
            # other non-essential results:
            'eval_time': timing}


# hp.uniform(label,low,high)参数在low和high之间均匀分布。
# hp.quniform(label,low,high,q),参数的取值round(uniform(low,high)/q)*q，适用于那些离散的取值。
def run_all_dl(csvfile=saving_fp,
               space=None):
    # maxout works well with dropout (Goodfellow et al 2013), and rectifier has worked well with image recognition (LeCun et al 1998)
    if space is None:
        space = [hp.quniform('h1', 100, 550, 1),  # quniform：离散均匀分布；uniform：连续均匀分布
                 hp.quniform('h2', 100, 550, 1),
                 hp.quniform('h3', 100, 550, 1),
                 # hp.choice('activation', ["RectifierWithDropout", "TanhWithDropout"]),
                 hp.uniform('hdr1', 0.001, 0.3),
                 hp.uniform('hdr2', 0.001, 0.3),
                 hp.uniform('hdr3', 0.001, 0.3),
                 hp.uniform('rho', 0.9, 0.999),
                 # 偏差
                 hp.uniform('epsilon', 1e-10, 1e-4)]
    start_save(csvfile=csvfile)
    # 每次结果放到这里
    trials = Trials()
    logging.debug("Deep learning...")
    # 在 objective 函数中寻求最小解（MSE），evals：执行次数
    best = fmin(objective,  # DNN函数
                space=space,
                algo=tpe.suggest,
                max_evals=evals,
                trials=trials)
    logging.debug(best)
    logging.debug(trials.losses())
    with open('output/dlbest.pkl', 'w') as output:
        pickle.dump(best, output, -1)
    with open('output/dltrials.pkl', 'w') as output:
        pickle.dump(trials, output, -1)


run_all_dl()

# Send email
email = False
if (email):
    import smtplib

    GMAIL_USERNAME = None
    GMAIL_PW = None
    RECIP = None
    SMTP_NUM = None
    session = smtplib.SMTP('smtp.gmail.com', SMTP_NUM)
    session.ehlo()
    session.starttls()
    session.login(GMAIL_USERNAME, GMAIL_PW)
    headers = "\r\n".join(["from: " + GMAIL_USERNAME,
                           "subject: " + "Finished running script: " + __file__,
                           "to: " + RECIP,
                           "mime-version: 1.0",
                           "content-type: text/html"])
    content = headers + "\r\n\r\n" + "Done running the script.\n Sent from my Python code."
    session.sendmail(GMAIL_USERNAME, RECIP, content)
