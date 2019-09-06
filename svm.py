import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures, MinMaxScaler, StandardScaler
import matplotlib.pyplot as plt
from matplotlib.dates import (YEARLY, DateFormatter,
                              rrulewrapper, RRuleLocator, drange)
import datetime
from sklearn import svm
from sklearn.linear_model import ElasticNet
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import StratifiedKFold, KFold
from sklearn.model_selection import learning_curve
from sklearn.kernel_ridge import KernelRidge
from sklearn.svm import SVR
import time
import sklearn
import seaborn as sns
import keras.backend as K
from keras.optimizers import SGD
from keras.layers import LSTM
from keras.layers import SimpleRNN as RNN
from keras.layers import Dropout
from keras.callbacks import EarlyStopping
from keras.models import load_model
from functions import *

param1 = 1.3
param2 = 0.15

## TAKE OPEN PRICE OF EVERYTHING EXCEPT FUTURES PRICE, FOR WHICH WE TRY TO PREDICT THE CLOSE


one_month = pd.read_excel('data/1 MONTH.xlsx', sheet_name = 0, index_col = 0).iloc[:,0]
two_month = pd.read_excel('data/2 MONTH.xlsx', sheet_name = 0, index_col = 0).iloc[:,0]
three_month = pd.read_excel('data/3 MONTH.xlsx', sheet_name = 0, index_col = 0).iloc[:,0]
four_month = pd.read_excel('data/4 month.xlsx', sheet_name = 0, index_col = 0).iloc[:,0]
five_month = pd.read_excel('data/5 month.xlsx', sheet_name = 0, index_col = 0).iloc[:,0]
six_month = pd.read_excel('data/6 month.xlsx', sheet_name = 0, index_col = 0).iloc[:,0]
fed = pd.read_excel('data/fed.xlsx', sheet_name = 0, index_col = 0).iloc[:,0]
dollar_index = pd.read_excel('data/dollar index 3.xlsx', sheet_name = 0, index_col = 0).iloc[:,1]
inventory = pd.read_excel('data/inventory.xlsx', sheet_name = 0, index_col = 0).iloc[:,0]
sp500 = pd.read_excel('data/s&p.xlsx', sheet_name = 0, index_col = 0).iloc[:,1]
production = pd.read_excel('data/WCRFPUS2w.xls', sheet_name = 0, index_col = 0).iloc[:,0]
inven_r = pd.read_excel('data/inven_r.xls', sheet_name = 0, index_col =0).iloc[:,0]
features = [one_month, two_month, three_month, four_month, five_month, six_month, fed, dollar_index, inventory, sp500, production]

df = one_month.copy()
features_2 = [two_month, three_month, four_month, five_month, six_month, fed, dollar_index, inventory, sp500, production]
for i in features_2:
    df = pd.concat([df, i], axis = 1)
df.columns = ['one_month', 'two_month', 'three_month', 'four_month', 'five_month', 'six_month', 'fed', 'dollar_index', 'inventory', 'sp500', 'production']
### FILLING IN BLANKS WITH PREVIOUS VALUES
df = df.fillna(method='ffill')
df = df[1000:5850]
### NEW FEATURE, PRODUCTION/INVENTORY
df['inventory'] = df['inventory'].shift(periods=1)
df['production'] = df['production'].shift(periods=1)
df['Ratio'] = df['inventory']/df['production']
### ONE DAY AHEAD RETURN (DAILY REBALANCING)

column_names = ['one_month', 'two_month', 'three_month', 'four_month', 'five_month', 'six_month', 'fed', 'dollar_index', 'inventory', 'sp500', 'production']

for d in column_names:
    df[d+' return'] = (df[d]/df.shift(periods=1)[d])-1


for d in column_names:
    df[d+' change'] = df[d]-df.shift(periods=1)[d]

df = df[1:-1]

### MOVING AVERAGE, 2 DAYS

### NOT USED

for d in column_names:
    df[d+' Movavg'] = df[d+' return'].rolling(window=2).mean().shift(periods=1)

df = df[5:-1]


column_names = ['one_month', 'two_month', 'three_month', 'four_month', 'five_month', 'six_month']
for d in column_names:
    df['Label '+d] = df[d+' return'].shift(periods=-1)
df = df[9:-1]


def hyper_search(month, features):

    train_length = int(0.8*len(month))

    x_train = features[:train_length]
    x_test = features[train_length:]
    label_train = month[:train_length]
    label_test = month[train_length:]

    scaler = StandardScaler()
    scaler = scaler.fit(x_train)

    x_train = scaler.transform(x_train)
    x_test = scaler.transform(x_test)

    C_range = 10. ** np.arange(-3, 6)
    print(C_range)
    gamma_range = 10. ** np.arange(-8, 3)
    print(gamma_range)

    param_grid = dict(gamma=gamma_range, C=C_range)

    svr = svm.SVR()

    clf = GridSearchCV(svr, param_grid, n_jobs = -1)
    clf.fit(x_train, label_train)

    print(clf.best_params_)

    pvt = pd.pivot_table(pd.DataFrame(clf.cv_results_),values='mean_test_score', index='param_C', columns='param_gamma')
    sns.heatmap(pvt)


    return clf
#
# features_dataset = df[['fed', 'dollar_index', 'sp500', 'inventory', 'production', 'Ratio']].values
# label = df['one_month'].values
# hyper_searcher = hyper_search(label, features_dataset)

def svm_regression(month, features):

    train_length = int(0.8*len(month))

    x_train = features[:train_length]
    x_test = features[train_length:]
    label_train = month[:train_length]
    label_test = month[train_length:]

    scaler = StandardScaler()
    scaler = scaler.fit(x_train)

    x_train = scaler.transform(x_train)
    x_test = scaler.transform(x_test)

    clf = svm.SVR(C = 9200, gamma = 0.000023)
    svm_model = clf.fit(x_train, label_train)

    predicted_y = svm_model.predict(x_test)

    return label_test, predicted_y

number = 0

final_svm = np.ones((967))

true_svm = np.ones((967))

column_names = ['one_month', 'two_month', 'three_month', 'four_month', 'five_month', 'six_month']

for d in column_names:

    number = number + 1

    features_dataset = df[['fed', 'dollar_index', 'sp500', 'inventory', 'production', 'Ratio', d +' Movavg']].values

    label = df[d].values

    true, prediction = svm_regression(label, features_dataset)

    final_svm = np.vstack((final_svm, prediction))

    true_svm = np.vstack((true_svm, true))

final_svm = np.transpose(final_svm)
true_svm = np.transpose(true_svm)

svm_trader = short_trader(final_svm[:600], true_svm[:600], param1, "price", inven_r[:600], param2)
