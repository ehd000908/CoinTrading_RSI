from webbrowser import get
import pyupbit
import time
import datetime
import pandas as pd
import numpy as np
import openpyxl
import telegram
from telegram.ext import Updater
from telegram.ext import MessageHandler, Filters
import requests
from bs4 import BeautifulSoup
import finterstellar as fs
import matplotlib.pyplot as plt
from scipy import interpolate
from pandas_datareader import data 

access = "vfFhqF1xjxeMwUxlDAqIH6Q77hygh3A6bJfyQBiQ"
secret = "25YQrCCvcz3of1hpdo4wNs2DRa0ibQvQ9sM1DY3f"

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("Autotrade Start")

# 텔레그램봇
token = "5381280171:AAGs86pwfWOaEHMl8odcNiZzcLfxIQRrj4k"
user_id = 5359786981
bot = telegram.Bot(token)
updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher

# 코인 관련 함수
# -------------------------------------------------------
class coin(object):

    def __init__(self,a):
        self.coin = a
        self.krw = "KRW"

    def get_balance(self):
        return upbit.get_balance(self.coin)

    def get_balance_krw(self):
        return upbit.get_balance(self.krw)

    def get_current_price(self):
        return pyupbit.get_current_price(self.coin)
    
    def get_minute_bar(self):
        return pyupbit.get_ohlcv(self.coin, "minute5")

    def get_avg_price(self):
        balances = upbit.get_balances()
        for i in balances:
            if i['currency'] == 'XRP':
                avg_buy_price = i["avg_buy_price"]
        return avg_buy_price
# -------------------------------------------------------

# 볼린저밴드
# ---------------------------------------------------------------------------------------------------
class Bollingerband(object):

    def __init__(self):
        self.coin = "KRW-BTC"
        self.mbb = pyupbit.get_ohlcv(self.coin, "minutes5")["close"].rolling(window = 20).mean()
        self.band = 2 * pyupbit.get_ohlcv(self.coin, "minutes5")["close"].rolling(window = 20).std(ddof = 0)
        self.ubb = self.mbb + self.band
        self.lbb = self.mbb - self.band

    def ubb_current(self):
        return self.ubb[199]

    def lbb_current(self):
        return self.lbb[199]
# ---------------------------------------------------------------------------------------------------

# 이동평균선
# 60 이동평균선 기울기 기준값
# ------------------------------------------------------
def ma60(ticker):
    v = pyupbit.get_ohlcv(ticker, "minutes5")["close"]

    c1 = v.rolling(60)
    ma60 = c1.mean()

    y_axis = []

    for i in range(0,199):
        y_axis.append(ma60[i])

    t1 = y_axis[-2]
    t2 = y_axis[-1]
    
    delta = t2-t1
    return delta
# ------------------------------------------------------

# 매매 일지 작성
# -----------------------------------------------------------
class write_trading_log(object):
    
    def __init__(self,a,b,c,d,e,f,g,h):
        self.wb = openpyxl.load_workbook("trading_log.xlsx")
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f
        self.g = g
        self.h = h

    def write_trade_log(self):
        sheet = (self.wb).active
        tpb = []
        tpb.append(self.a)
        tpb.append(self.b)
        tpb.append(self.c)
        tpb.append(self.d)
        tpb.append(self.e)
        tpb.append(self.f)
        tpb.append(self.g)
        tpb.append(self.h)
        sheet.append(tpb)
        (self.wb).save("trading_log.xlsx")
#-----------------------------------------------------------
    
# 정보 저장
# 초기 원화 잔고 - 기준 매수 시간 - 축적 매수량 - 평균 매수가
#---------------------------------------------------------
class save(object):

    def __init__(self,a,b,c,d):
        self.a = a
        self.b = b
        self.c = c
        self.d = d

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
        f = open("avg_buy_price.txt", "w")
        f.write(str(self.d))
        f.close()
# ------------------------------------------------------

# 정보 읽기
# 초기 원화 잔고 - 기준 매수 시간 - 축적 매수량 - 평균 매수가
# --------------------------------------------------------------------
class read(object):

    def __init__(self):
        self.a = 0

    def read_first_krw(self):
        f = open("krw_balance.txt", "r")
        first_krw_balance = float(f.readline())
        f.close()
        return first_krw_balance

    def read_after_time(self):
        f = open("trade_time.txt", "r")
        line = f.readline()
        ttime = datetime.datetime.strptime(line, "%Y-%m-%d %H:%M:%S")
        f.close()
        return ttime
    
    def read_accumulated_volume(self):
        f = open("accumulated_volume.txt", "r")
        accumulated_volume = float(f.readline())
        f.close()
        return accumulated_volume

    def read_avg_price(self):
        f = open("avg_buy_price.txt", "r")
        avg_buy_price = float(f.readline())
        f.close()
        return avg_buy_price
# --------------------------------------------------------------------

# 텔레그램 봇 함수
# -------------------------------------------------------------------------
def send_message_bot(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="지금")
# -------------------------------------------------------------------------

# RSI 함수
# -----------------------------------------------------------------------
class RSI(object):
    
    def __init__(self,a):

        self.coin = a

        df = pyupbit.get_ohlcv(a, "minute5")

        df['변화량'] = df['close'] - df['close'].shift(1)
        df['상승폭'] = np.where(df['변화량'] >= 0, df['변화량'], 0)
        df['하락폭'] = np.where(df['변화량'] < 0, df['변화량'].abs(), 0)

        df['AU'] = df['상승폭'].ewm(alpha=1/7, min_periods=7).mean()
        df['AD'] = df['하락폭'].ewm(alpha=1/7, min_periods=7).mean()

        df['RSI'] = df['AU'] / (df['AU'] + df['AD']) * 100

        self.rsi_n = df['RSI'][-1]
        self.rsi_b = df['RSI'][-2]

    def now_rsi(self):
        return self.rsi_n
    
    def before_rsi(self):
        return self.rsi_b
# -----------------------------------------------------------------------

btc = "KRW-BTC"
rsi = RSI(btc)
c = coin(btc)
r = read()
bol = Bollingerband()
st = -7000

# -----------------------------------------------------------------------

df = pyupbit.get_ohlcv(btc, "minute5")

print(df[-12:])