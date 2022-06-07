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


access = ""
secret = ""

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("Autotrade Start")


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
    
    def __init__(self,a,b,c,d,e,f,g):
        self.wb = openpyxl.load_workbook("trading_log.xlsx")
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f
        self.g = g

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
        sheet.append(tpb)
        (self.wb).save("trading_log.xlsx")
#-----------------------------------------------------------
    
# 정보 저장
# 초기 원화 잔고 - 기준 매수 시간 - 축적 매수량 - 평균 매수가
#---------------------------------------------------------
class save(object):

    def __init__(self,a,b,c,d,e):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e

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

    def save_counting(self):
        f = open("counting.txt", "w")
        f.write(str(self.e))
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
    
    def read_counting(self):
        f = open("counting.txt", "r")
        counting = float(f.readline())
        f.close()
        return counting
# --------------------------------------------------------------------

# 텔레그램 봇 함수
# -------------------------------------------------------------------------
def send_message_bot(update, context):

    avg_buy_price = r.read_avg_price()
    accumulated_volume = r.read_accumulated_volume()
    now_earning_rate = round((c.get_current_price() - avg_buy_price) / avg_buy_price * 100, 2)

    r1 = "현재 수익률 : " + str(now_earning_rate) + " %\n"
    r2 = "현재 수익금 : " + str(round(accumulated_volume * now_earning_rate / 100)) + " KRW\n"
    r3 = "기준 수익금 : " + str(round((c.get_balance()*c.get_current_price()*0.9985) - accumulated_volume))+ " KRW\n"
    r4 = "현재가 : " + str(round(c.get_current_price())) + " KRW\n"

    if round(accumulated_volume * now_earning_rate / 100) > 0:

        r5 = "수익중"

    else:

        r5 = "손실중"

    w = r1+r2+r3+r4+r5

    context.bot.send_message(chat_id=update.effective_chat.id, text=w)
   
# -------------------------------------------------------------------------


btc = "KRW-BTC"
r = read()
c = coin(btc)
st = -5000

df = pyupbit.get_ohlcv(btc, "minute5", count=10000, period =1)
#df = pyupbit.get_ohlcv(btc, interval="minute5", count=600, period=1)

df['변화량'] = df['close'] - df['close'].shift(1)
df['상승폭'] = np.where(df['변화량'] >= 0, df['변화량'], 0)
df['하락폭'] = np.where(df['변화량'] < 0, df['변화량'].abs(), 0)

df['AU'] = df['상승폭'].ewm(alpha=1/7, min_periods=7).mean()
df['AD'] = df['하락폭'].ewm(alpha=1/7, min_periods=7).mean()
df['매수가'] = ""
df['매수평균가'] = ""
df['매수금액'] = ""
df['매수누적금액'] = ""
df['매도가'] = ""
df['수익금'] = ""
df['수익률'] = ""
df['누적수익률'] = ""
df['원화잔고'] = ""

df['RSI'] = df['AU'] / (df['AU'] + df['AD']) * 100

before_rsi = df['RSI'][-2]
now_rsi = df['RSI'][-1]
# ----------------------------------------------------------------------

k = 0
fee = 0.9995
vv = 10000
counting = 1
krw = 1000000
tt = 30

f = open("krw_rsi.txt", "w")
f.write(str(krw))
f.close()

for i in range(7,9999):

    if k == 0:
        

        # 첫 매수
        if df['RSI'][i-1] < tt and df['RSI'][i-1] < df['RSI'][i]:

            f = open("krw_rsi.txt", "r")
            kk = float(f.readline())
            f.close()
            
            buy = df['open'][i]
            df['매수가'][i] = buy
            df['매수평균가'][i] = buy

            f = open("backtest_buy_avg.txt", "w")
            f.write(str(buy))
            f.close()

            vol = kk/20
            df['매수금액'][i] = vol
            df['매수누적금액'][i] = vol
            counting = counting + 1

            f = open("backtest_acum_price.txt", "w")
            f.write(str(vol))
            f.close()

            k = 1
        
        
    else:
        #평균가
        f = open("backtest_buy_avg.txt", "r")
        bb = float(f.readline())
        f.close()

        #매수할금액
        f = open("backtest_acum_price.txt", "r")
        bp = float(f.readline())
        f.close()

        # 원화 보유
        f = open("krw_rsi.txt", "r")
        kk = float(f.readline())
        f.close()

        # 매수 누적 금액
        f = open("backtest_acum_price.txt", "r")
        acum = float(f.readline())
        f.close()

        # 추가매수
        if (-(bb - df['open'][i])) / bb*100 < -1 and df['RSI'][i-1] < tt and df['RSI'][i-1] < df['RSI'][i]:

            if bp < kk:   

                buy = df['open'][i]
                df['매수가'][i] = buy


                df['매수평균가'][i] = (buy + bb)/2

                f = open("backtest_buy_avg.txt", "w")
                f.write(str((buy + bb)/2))
                f.close()


                df['매수금액'][i] = bp
                df['매수누적금액'][i] = 2*bp 

                f = open("backtest_acum_price.txt", "w")
                f.write(str(2*bp))
                f.close()

                counting = counting + 1

            if bp > kk:

                buy = df['open'][i]
                df['매수가'][i] = buy


                ttt = ((buy*(kk-acum))+(bb*acum))/kk

                df['매수평균가'][i] = ttt

                f = open("backtest_buy_avg.txt", "w")
                f.write(str(ttt))
                f.close()


                df['매수금액'][i] = kk-acum
                df['매수누적금액'][i] = kk

                f = open("backtest_acum_price.txt", "w")
                f.write(str(kk))
                f.close()

                counting = counting + 1

        # 매도
        if df['RSI'][i-1] > 80 and df['RSI'][i-1] > df['RSI'][i]:

            sell = df['open'][i]
            df['매도가'][i] = sell

            f = open("backtest_buy_avg.txt", "r")
            ab = float(f.readline())
            f.close()

            f = open("backtest_acum_price.txt", "r")
            acum_price = float(f.readline())
            f.close()

            earning_rate = (sell - ab)/ab
            earning = earning_rate * acum_price

            df['수익금'][i] = earning
            df['수익률'][i] = earning_rate*100

            df['누적수익률'][i] = df['수익률'][i].cumprod()

            f = open("krw_rsi.txt", "r")
            acum_krw = float(f.readline())
            f.close()
            
            akrw = acum_krw + earning

            df['원화잔고'][i] = akrw


            f = open("krw_rsi.txt", "w")
            f.write(str(akrw))
            f.close()

            f = open("backtest_buy_avg.txt", "w")
            f.write(str(0))
            f.close()

            k = 0
            counting = 1

        if acum == kk and (-(bb - df['low'][i])) / bb*100 < -5:

            sell = df['low'][i]
            df['매도가'][i] = sell

            f = open("backtest_buy_avg.txt", "r")
            ab = float(f.readline())
            f.close()

            f = open("backtest_acum_price.txt", "r")
            acum_price = float(f.readline())
            f.close()

            earning_rate = (sell - ab)/ab
            earning = earning_rate * acum_price

            df['수익금'][i] = earning
            df['수익률'][i] = earning_rate*100

            df['누적수익률'][i] = df['수익률'][i].cumprod()

            f = open("krw_rsi.txt", "r")
            acum_krw = float(f.readline())
            f.close()
            
            akrw = acum_krw + earning

            df['원화잔고'][i] = akrw


            f = open("krw_rsi.txt", "w")
            f.write(str(akrw))
            f.close()

            f = open("backtest_buy_avg.txt", "w")
            f.write(str(0))
            f.close()

            k = 0
            counting = 1

df.to_excel("backtest_RSI.xlsx")
