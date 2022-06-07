from sys import meta_path
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

# 텔레그램봇
token = ""
user_id = 
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
            if i['currency'] == 'BTC':
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
r = read()
rsi = RSI(btc)
c = coin(btc)
st = -5000
tt = 30

while True:
    
    try:

        df = pyupbit.get_ohlcv(btc, "minute5")

        df['변화량'] = df['close'] - df['close'].shift(1)
        df['상승폭'] = np.where(df['변화량'] >= 0, df['변화량'], 0)
        df['하락폭'] = np.where(df['변화량'] < 0, df['변화량'].abs(), 0)

        df['AU'] = df['상승폭'].ewm(alpha=1/7, min_periods=7).mean()
        df['AD'] = df['하락폭'].ewm(alpha=1/7, min_periods=7).mean()

        df['RSI'] = df['AU'] / (df['AU'] + df['AD']) * 100

        now_rsi = df['RSI'][-1]
        before_rsi = df['RSI'][-2]

        # 첫 매수
        # RSI 꺾인 지점이 25미만이면 매수
        if before_rsi < tt and before_rsi < now_rsi and c.get_balance() == 0:

            if c.get_balance_krw() > 0:

                #최초 원화 잔고 저장
                fir_krw = c.get_balance_krw()
                s = save(fir_krw,0,0,0,0)
                s.save_first_krw()

                vol = fir_krw / 20

                upbit.buy_market_order(btc, vol*0.9995) # 매수 시 수수료 0.05%

                # 텔레그램 봇으로 알림
                bot.sendMessage(chat_id=user_id, text="첫 매수 완료")

                # 매수 한 시간
                t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # 매수 한 다음 5분봉 기준 시간
                after_time = c.get_minute_bar().iloc[[199]].index[0] + datetime.timedelta(minutes=5)

                # 평균 매수가
                ap = float(c.get_avg_price())

                # 누적 매수량
                accumulated_volume = vol*0.9995

                # 정보 저장
                s = save(0,after_time,accumulated_volume,ap,1)
                s.save_after_time()
                s.save_accumulated_volume()
                s.save_avg_price()
                s.save_counting()

                # 매매일지 작성
                wtl = write_trading_log(t, accumulated_volume, ap, accumulated_volume, "", "", r.read_first_krw())
                wtl.write_trade_log()

        # 현 상태 표시
        if c.get_balance() == 0:

            print("매수 대기중")
            print(c.get_current_price())
        
        else:
            
            # 매수 한 다음 5분봉부터 재매수 시작, 5분봉 1개마다 매수 한 번
            # 매수 한 다음 5분봉, 코인 잔고 있으면

            print("-------코인 보유중-------")
            
            first_krw_balance = r.read_first_krw()
            vol = first_krw_balance / 20
            after_time = r.read_after_time()
            accumulated_volume = r.read_accumulated_volume()
            avg_buy_price = r.read_avg_price()
            counting = r.read_counting()
            now_earning_rate = round((c.get_current_price() - avg_buy_price) / avg_buy_price * 100, 2)

            # 현재 수익률(%)

            print("현재 수익률:", now_earning_rate,"%")
            print("현재 수익금:", round(accumulated_volume * now_earning_rate / 100), "KRW")
            print("기준 수익금:", round((c.get_balance()*c.get_current_price()*0.998) - accumulated_volume), "KRW")
            print("현재가 :", round(c.get_current_price()), "KRW")
            print(accumulated_volume)
            start_handler = MessageHandler(Filters.text & (~Filters.command), send_message_bot)
            dispatcher.add_handler(start_handler)

            updater.start_polling()

            if after_time < datetime.datetime.now():
                
                 # 손실률
                dd = pyupbit.get_ohlcv(btc, "day")

                if (c.get_current_price() - dd['close'][-2]) / dd['close'][-2] * 100 < -3:
                
                    mp = -2

                else:

                    mp = -1
                
                # 손실률 1% 이하이고 RSI 꺾인 부분 25 이하이면 현재 보유 수량만큼 추가 매수
                if now_earning_rate < float(mp):
                    
                    if before_rsi < tt and before_rsi < now_rsi:
                        
                        # 첫번째 추가 매수
                        if counting == 1:

                            upbit.buy_market_order(btc, vol*0.9995) # 매수 시 수수료 0.05%

                            # 텔레그램 봇으로 알림
                            bot.sendMessage(chat_id=user_id, text="추가 매수 완료")

                            # 매수 한 시간
                            t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                            # 매수 한 다음 5분봉 기준 시간
                            after_time = c.get_minute_bar().iloc[[199]].index[0] + datetime.timedelta(minutes=5)
        
                            # 평균 매수가
                            ap = float(c.get_avg_price())

                            # 축적 매수량
                            accumulated_volume = r.read_accumulated_volume() + vol*0.9995

                            # 정보 저장
                            s = save(0,after_time,accumulated_volume,ap,counting+1)
                            s.save_after_time()
                            s.save_accumulated_volume()
                            s.save_avg_price()
                            s.save_counting()

                            # 매매일지 작성
                            wtl = write_trading_log(t, vol*0.9995, ap, accumulated_volume, "", "", r.read_first_krw())
                            wtl.write_trade_log()


                        # 매수 3번째 이상
                        if counting > 1.0:
            
                            if c.get_balance_krw() > vol*(2**(counting-1))*0.9995:

                                upbit.buy_market_order(btc, vol*(2**(counting-1))*0.9995) # 매수 시 수수료 0.05%

                                # 텔레그램 봇으로 알림
                                bot.sendMessage(chat_id=user_id, text="추가 매수 완료")

                                # 매수 한 시간
                                t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                                # 매수 한 다음 5분봉 기준 시간
                                after_time = c.get_minute_bar().iloc[[199]].index[0] + datetime.timedelta(minutes=5)

                                # 평균 매수가
                                ap = float(c.get_avg_price())

                                # 축적 매수량
                                accumulated_volume = r.read_accumulated_volume() + vol*(2**(counting-1))*0.9995

                                # 정보 저장
                                s = save(0,after_time,accumulated_volume,ap,counting+1)
                                s.save_after_time()
                                s.save_accumulated_volume()
                                s.save_avg_price()
                                s.save_counting()

                                # 매매일지 작성
                                wtl = write_trading_log(t, vol*(2**(counting-1))*0.9995, ap, accumulated_volume, "", "", r.read_first_krw())
                                wtl.write_trade_log()


                            # 물 탈 금액 부족할 때 최종 매수
                            if 5000 < c.get_balance_krw() < vol*(2**(counting-1))*0.9995:

                                fb = c.get_balance_krw()*0.9995

                                upbit.buy_market_order(btc, fb) # 매수 시 수수료 0.05%

                                # 텔레그램 봇으로 알림
                                bot.sendMessage(chat_id=user_id, text="최종 매수 완료")

                                # 매수 한 시간
                                t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                                # 매수 한 다음 5분봉 기준 시간
                                after_time = c.get_minute_bar().iloc[[199]].index[0] + datetime.timedelta(minutes=5)

                                # 평균 매수가
                                ap = float(c.get_avg_price())

                                # 축적 매수량
                                accumulated_volume = r.read_accumulated_volume() + c.get_balance_krw*0.9995


                                # 정보 저장
                                s = save(0,after_time,accumulated_volume,ap,counting+1)
                                s.save_after_time()
                                s.save_accumulated_volume()
                                s.save_avg_price()
                                s.save_counting()

                                # 매매일지 작성
                                wtl = write_trading_log(t, fb, ap, accumulated_volume, "", "", r.read_first_krw())
                                wtl.write_trade_log()
            else:
                print("아직 다음봉 갱신 안 됨")


            # RSI 꺾인 지점 70 이상이면 전량 시장가 매도
            if before_rsi > 70 and before_rsi > now_rsi:

                if (c.get_balance()*c.get_current_price()*0.998) - accumulated_volume > 0:

                    upbit.sell_market_order(btc, c.get_balance())

                    # 최종 수익률
                    earning = c.get_balance_krw() - first_krw_balance
                    earning_rate = earning / first_krw_balance

                    # 텔레그램 봇으로 알림
                    s1 = "전량 익절 완료 \n"
                    s2 = "최종 수익률 : " + str(earning_rate) + " %\n"
                    s3 = "최종 수익금 : " + str(earning) + " KRW"

                    ss = s1+s2+s3

                    bot.sendMessage(chat_id=user_id, text=ss)


                    # 매도 시간
                    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


                    # 매매일지 작성
                    wtl = write_trading_log(t, "", "", "", earning, earning_rate, c.get_balance_krw())
                    wtl.write_trade_log()


            # 원화 잔고 부족, 손실률 몇 % 이하시 전량 시장가 매도
            if c.get_balance_krw() < 5000:

                # 손실률(%)
                dd = pyupbit.get_ohlcv(btc, "day")

                if (c.get_current_price() - dd['close'][-2]) / dd['close'][-2] * 100 < -3:
                
                    loss = -5

                else:

                    loss = -3
                
                if (c.get_current_price() - avg_buy_price) / avg_buy_price * 100 < float(loss) and c.get_balance_krw() < 5000:

                    upbit.sell_market_order(btc, c.get_balance())

                    # 최종 수익률
                    earning = c.get_balance_krw() - first_krw_balance
                    earning_rate = earning / first_krw_balance

                    # 텔레그램 봇으로 알림
                    s1 = "전량 손절 완료 \n"
                    s2 = "최종 수익률 : " + str(earning_rate) + " %\n"
                    s3 = "최종 수익금 : " + str(earning) + " KRW"

                    ss = s1+s2+s3
                    
                    bot.sendMessage(chat_id=user_id, text=ss)

                    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    # 매매일지 작성
                    wtl = write_trading_log(t, "", "", "", earning, earning_rate, c.get_balance_krw())
                    wtl.write_trade_log()

                

        time.sleep(0.2)      
        
    except Exception as e:
        print(e)

    time.sleep(0.2)    
