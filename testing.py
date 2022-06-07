from itertools import accumulate
import json
from webbrowser import get
import pyupbit
import time
import datetime
import pandas as pd
import json
import random
import numpy
import openpyxl

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

# 시가
def open_price(ticker, num):
    open = get_minute_bar(ticker).iloc[[num]]["open"]
    return open[0]

# 고가
def high_price(ticker, num):
    high = get_minute_bar(ticker).iloc[[num]]["high"]
    return high[0]

# 저가
def low_price(ticker, num):
    low = get_minute_bar(ticker).iloc[[num]]["low"]
    return low[0]

# 종가
def close_price(ticker, num):
    close = get_minute_bar(ticker).iloc[[num]]["close"]
    return close[0]

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
# ---------------
coin = "KRW-BTC"
# ---------------

while True:

    try:
        # 매매 중 매매일지 작성
        wb = openpyxl.load_workbook("trading_log.xlsx")
        sheet = wb.active

        # 볼린저밴드
        # ----------------------------------------------------------------------------------
        w = 20 # 기준 이동평균일
        k = 2 # 기준 상수

        # 중심선 MBB
        mbb = pyupbit.get_ohlcv(coin, "minutes5")["close"].rolling(window = w).mean()

        # 표준편차
        band = k * pyupbit.get_ohlcv(coin, "minutes5")["close"].rolling(window = w).std()

        # 상한선 UBB
        ubb = mbb + band
        ubb_current = ubb[199]

        # 하한선 LBB
        lbb = mbb - band
        lbb_current = lbb[199]
        # ----------------------------------------------------------------------------------

        # 현재 원화 잔고
        krw = get_balance("KRW")

        # 첫 매수
        # 볼린저밴드 하한선 이탈 시 잔고의 1/20만큼 시장가 매수
        if get_current_price(coin) < lbb_current and get_balance(coin) == 0 and (krw/20)*0.9995 > 5000:
            if krw > 0:

                # 최초 원화 잔고 저장
                kkk = str(krw)
                f = open("krw_balance.txt", "w")
                f.write(kkk)
                f.close()

                upbit.buy_market_order(coin, (krw/20)*0.9995) # 매수 시 수수료 0.05%
                t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # 매수 한 다음 5분봉 기준 시간
                after_time = str(get_minute_bar(coin).iloc[[199]].index[0] + datetime.timedelta(minutes=5))

                # 최초 매수 시간 저장
                f = open("trade_time.txt", "w")
                f.write(after_time)
                f.close()


                f = open("krw_balance.txt", "r")
                first_krw_balance = float(f.readline())
                f.close()

                accumulated_volume = str((first_krw_balance/20)*0.9995)

                # 축적된 매수 금액 저장
                f = open("accumulated_volume.txt", "w")
                f.write(accumulated_volume)
                f.close()

                # 평균 매수가
                balances = upbit.get_balances()
                for i in balances:
                    if i['currency'] == 'BTC':
                        avg_buy_price = str(i["avg_buy_price"])

                        f = open("avg_buy_price.txt", "w")
                        f.write(avg_buy_price)
                        f.close()

                tpb = []
                tpb.append(t)
                tpb.append(float(avg_buy_price))
                tpb.append(float(accumulated_volume))
                tpb.append(float(avg_buy_price))
                tpb.append(float(accumulated_volume))
                sheet.append(tpb)
                wb.save("trading_log.xlsx")
                tpb = []


        # 현 상태 표시
        if get_balance(coin) == 0:
            print("매수 대기중")
        else:
            print("코인 보유중")
    

        # 매수 한 다음 5분봉부터 재매수 시작, 5분봉 1개마다 매수 한 번
        # 매수 한 다음 5분봉, 코인 잔고 있으면
        if get_balance(coin) > 0:
        
            # 최초 매수 시간 불러오기
            f = open("trade_time.txt", "r")
            line = f.readline()
            ttime = datetime.datetime.strptime(line, "%Y-%m-%d %H:%M:%S")
            f.close()

            # 평균 매수가 불러오기
            f = open("avg_buy_price.txt", "r")
            avg_buy_price = float(f.readline())
            f.close()

            # 최초 원화 잔고 불러오기
            f = open("krw_balance.txt", "r")
            first_krw_balance = float(f.readline())
            f.close()

            # 누적 매수 금액 불러오기
            f = open("accumulated_volume.txt", "r")
            accumulated_volume = float(f.readline())
            f.close()

            if ttime < datetime.datetime.now():

                # 마이너스 수익률(%)
                # -----------------
                mp = -0.5
                # -----------------

                # 마이너스 수익률 몇 % 이하이고 볼린저밴드 하한선 재 이탈 시 기존 잔고의 1/20만큼 추가 매수
                if ((get_current_price(coin) - avg_buy_price) / avg_buy_price) * 100 < float(mp) and krw > 5000:

                    print("손실중")

                    if get_current_price(coin) < lbb_current:
                        upbit.buy_market_order(coin, (first_krw_balance/20)*0.9995)
                        t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        # 매수 한 다음 5분봉 기준 시간
                        after_time = str(get_minute_bar(coin).iloc[[199]].index[0] + datetime.timedelta(minutes=5))

                        # 추가 매수 시간 저장
                        f = open("trade_time.txt", "w")
                        f.write(after_time)
                        f.close()


                        # 평균 매수가 갱신
                        balances = upbit.get_balances()
                        for i in balances:
                            if i['currency'] == 'BTC':
                                avg_buy_price = str(i["avg_buy_price"])

                                f = open("avg_buy_price.txt", "w")
                                f.write(avg_buy_price)
                                f.close()

                        # 추가 매수가
                        nn = upbit.get_order(coin, state="done")
                        new_buy = nn[0]["price"]

                        # 총 매수 금액 갱신
                        total_volume = str(accumulated_volume + (first_krw_balance/20)*0.9995)

                        f = open("accumulated_volume.txt", "w")
                        f.write(total_volume)
                        f.close()


                        tpb = []
                        tpb.append(t)
                        tpb.append(new_buy)
                        tpb.append((first_krw_balance/20)*0.9995)
                        tpb.append(avg_buy_price)
                        tpb.append(total_volume)
                        sheet.append(tpb)
                        wb.save("trading_log.xlsx")
                        tpb = []


            # 볼린저밴드 상한선 이탈 시 전량 시장가 매도
            if (get_current_price(coin) - avg_buy_price) > 0:

                print("수익중")

                if get_current_price(coin) > ubb_current:

                    upbit.sell_market_order(coin, get_balance(coin))
                    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    tpb = []
                    tpb.append(t)
                    tpb.append(0)
                    tpb.append(0)
                    tpb.append(0)
                    tpb.append(0)

                    # 최종 수익률(%)
                    earning = get_balance("KRW") - first_krw_balance
                    earning_rate = earning/first_krw_balance*100 

                    tpb.append(earning)
                    tpb.append(earning_rate)

                    # 총 금액

                    tpb.append(get_balance("KRW"))
                    sheet.append(tpb)
                    wb.save("trading_log.xlsx")
                    tpb = []
        
            # 마이너스 수익률 몇 % 이하시 전량 시장가 매도

            # 손실률(%)
            # -----------
            loss = -3
            # -----------

            if (get_current_price(coin) - avg_buy_price) / avg_buy_price * 100 < float(loss) and krw < 5000:

                upbit.sell_market_order(coin, get_balance(coin))
                t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                tpb = []
                tpb.append(t)
                tpb.append(0)
                tpb.append(0)
                tpb.append(0)
                tpb.append(0)

                # 최종 수익률(%)
                earning = get_balance("KRW") - first_krw_balance
                earning_rate = earning/first_krw_balance*100 

                tpb.append(earning)
                tpb.append(earning_rate)

                # 총 금액

                tpb.append(get_balance("KRW"))
                sheet.append(tpb)
                wb.save("trading_log.xlsx")
                tpb = []

        time.sleep(0.5)
    
    except Exception as e:
        print(e)
        time.sleep(0.5)
