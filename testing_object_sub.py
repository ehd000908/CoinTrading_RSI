from itertools import accumulate
import json
from this import d
from webbrowser import get
import pyupbit
import time
import datetime
import pandas as pd
import json
import random
import numpy
import openpyxl
import requests
import pprint
import numpy as np
import matplotlib.pyplot as plt

access = "vfFhqF1xjxeMwUxlDAqIH6Q77hygh3A6bJfyQBiQ"
secret = "25YQrCCvcz3of1hpdo4wNs2DRa0ibQvQ9sM1DY3f"

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("Autotrade Start")

# 현재 시간 조회
now = datetime.datetime.now()


# 코인 관련 함수
class coin(object):

    def __init__(self):
        self.coin = "KRW-BTC"

    def get_balance(self):
        return upbit.get_balance(self.coin)
    
    def get_current_price(self):
        return pyupbit.get_current_price(self.coin)
    
    def get_minute_bar(self):
        return pyupbit.get_ohlcv(self.coin, "minute5")

# 볼린저밴드
class Bollingerband(coin):

    def __init__(self):
        self.coin = "KRW-BTC"
        self.mbb = pyupbit.get_ohlcv(self.coin, "minutes5")["close"].rolling(window = 20).mean()
        self.band = 2 * pyupbit.get_ohlcv(self.coin, "minutes5")["close"].rolling(window = 20).std()
        self.ubb = self.mbb + self.band
        self.lbb = self.mbb - self.band

    def ubb_current(self):
        return self.ubb[199]

    def lbb_current(self):
        return self.lbb[199]
    
    
# 정보 저장
# 초기 원화 잔고 - 기준 매수 시간 - 축적 매수량 - 평균 매수가
class save(object):

    def __init__(self,a,b,c):
        self.a = a
        self.b = b
        self.c = c

    def save_first_krw(self):
        f = open("krw_balance.txt", "w")
        f.write(str(self.a))
        f.close()
    
    def save_after_time(self):
        f = open("trade_time.txt", "w")
        f.write(str(self.b))
        f.close()
    
    def save_accumulated_volume(self):
        f = open("accumulated_volume.txt", "w")
        f.write(str(self.c))
        f.close()

    def save_avg_price(self):
        balances = upbit.get_balances()
        for i in balances:
            if i['currency'] == 'BTC':
                avg_buy_price = i["avg_buy_price"]

                f = open("avg_buy_price.txt", "w")
                f.write(str(avg_buy_price))
                f.close()

# 이평선
def moving_average(ticker):
    ma = pyupbit.get_ohlcv(ticker, "minutes5")["close"]
    return ma

v = moving_average("KRW-BTC")

c1 = v.rolling(60)
ma5 = c1.mean()

x_axis = []
y_axis = []

for i in range(0,199):
    x_axis.append(ma5.index[i])
    y_axis.append(ma5[i])

t1 = y_axis[-3]
t2 = y_axis[-2]

delta = t2-t1

df = [0]

for i in range(0,198):
    k = y_axis[i+1]-y_axis[i]
    df.append(k)

for i in range(0,59):
    df[i] = 0

sum = 0

pprint.pprint(df)
pprint.pprint(x_axis)
for i in range(0,198):

    sum = sum + df[i]

avg = sum/199

print(delta)
plt.plot(x_axis, df)
plt.show()

print(delta)

