import json
import pyupbit
import time
import datetime
import pandas as pd
import json
import random
import numpy
import openpyxl
import pprint


access = ""
secret = ""

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("Autotrade Start")

# 함수 모음
# ------------------------------------------------------------

# 잔고 조회 - 개별 보유 수량
def get_balance(ticker):
    balances = upbit.get_balance(ticker)
    return balances

# 잔고 조회 - 보유 중인 모든 잔고 및 단가 정보
def get_balance_info(ticker):
    balances = upbit.get_balances()
    for i in balances:
        if i['currency'] == 'BTC':
            avg_buy_price = i["avg_buy_price"]
            return avg_buy_price

# 현재 시간 조회
now = datetime.datetime.now()

# 이전 봉 시간 조회
def get_before_time(ticker, num):
    df = pyupbit.get_ohlcv(ticker, "minute5")
    time = df.index[num]
    return time

# 5분봉 조회 - 200개분
def get_minute_bar(ticker):
    minute5 = pyupbit.get_ohlcv(ticker, "minute5")
    return minute5

# 현재가 조회
def get_current_price(ticker):
    price = pyupbit.get_current_price(ticker)
    return price

# 이평선
def moving_average(ticker,num):
    ma = pyupbit.get_ohlcv(ticker, "minutes5", count=num)["close"]
    i = 0
    sum = 0
    for i in range(0,num):
        sum = sum + ma[i]
    return sum/num
    
# ------------------------------------------------------------

# 코인 종류
coin = "KRW-BTC"

num = 199

# ----------------------------------------------------------------------------------
w = 20 # 기준 이동평균일
k = 2 # 기준 상수

    # 중심선 MBB
mbb = pyupbit.get_ohlcv(coin, "minutes5")["close"].rolling(window = w).mean()
mbb = mbb[199]

    # 표준편차
band = k * pyupbit.get_ohlcv(coin, "minutes5")["close"].rolling(window = w).std()

    # 상한선 UBB
ubb = mbb + band
ubb_current = ubb[199]

    # 하한선 LBB
lbb = mbb - band
lbb_current = lbb[199]
# ----------------------------------------------------------------------------------


a = get_minute_bar(coin).iloc[[199]].index[0]

tml = a + datetime.timedelta(minutes=5)

#print(now)

#print(a)
#print(tml)


kk = upbit.get_order("KRW-BTC", state="done")

aaa = upbit.get_order(coin, state="done")[0]

bb = aaa["created_at"]

asd = get_minute_bar(coin).iloc[[199]].index[0]

after_time = str(get_minute_bar(coin).iloc[[199]].index[0] + datetime.timedelta(minutes=5))



f = open("trade_time.txt", "r")
line = f.readline()
after_time = datetime.datetime.strptime(line, "%Y-%m-%d %H:%M:%S")
f.close()

if after_time < now:
    print("true")
