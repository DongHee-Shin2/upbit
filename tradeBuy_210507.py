import time
import pyupbit
import datetime

access = "accesskey"
secret = "secretkey"

BUY_UNIT_PRICE = 50000   # 처음 매수 금액
BUY_HAVE_COUNT = 20     # 보유 종목
SALE_UP_PER = 1.1

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_yday_ma_price(ticker,ma):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=ma)
    ma = df['close'].rolling(ma).mean().iloc[-1]
    return ma

def get_ma_price(ticker,ma):
    """이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=ma-1)
    res = df['close'].sum()
    current_price = get_current_price(ticker)
    res = (res + current_price) /ma
    return res

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0

def get_avg_buy_price(market):
    """평단가 조회"""
    ticker = market.replace("KRW-","")
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['avg_buy_price'] is not None:
                return float(b['avg_buy_price'])
            else:
                return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def get_up_per(market):
    """수익율"""
    current_price = get_current_price(market)
    buy_avg_price = get_avg_buy_price(market)
    ret = ((current_price - buy_avg_price) / buy_avg_price)*100
    ret -= 0.2 
    return ret

def get_gap_up_per(aPrice, bPrice):
    """수익률 계산"""
    ret = ((aPrice - bPrice) / bPrice)*100
    return ret

def get_buy_list():
    """보유종목"""
    ret = []
    balances = upbit.get_balances()
    for b in balances:
        # print(b)
        if b['currency'] != "KRW":
            ret.append(b)
    return ret

def isNaN(num):
    return num != num

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")


# 종목 리스트
import requests
URL = 'https://api.upbit.com/v1/market/all?isDetails=false'
response = requests.get(URL)
# print(response.status_code)
# print(response.text)

import json
targets = json.loads(response.text)
# y = json.dumps(response.text)
# print(y[0])

# 자동매매 시작
sell_count = 0
while True:
    for target in targets:
        time.sleep(0.3)
        try:
            market = target['market']
            if market.find('KRW') != -1 and market.find('USDT') == -1:
                print("")
                print(market)
                now = datetime.datetime.now()
                # start_time = get_start_time(market)
                # end_time = start_time + datetime.timedelta(days=1)

                # if start_time < now < end_time - datetime.timedelta(seconds=10):
                target_price = get_target_price(market, 0.2)
                current_price = get_current_price(market)
                buy_avg_price = get_avg_buy_price(market)
                # print("                      target_price")
                print(target_price)
                # print("                      current_price")
                print(current_price)

                upper = get_up_per(market)
                if upper > SALE_UP_PER:
                    print(">>>>> sale")
                    btc_balance = upbit.get_balance(market)
                    upbit.sell_market_order(market, btc_balance)

                elif target_price < current_price:
                    buys = get_buy_list()
                    krw = get_balance("KRW")
                    if krw > BUY_UNIT_PRICE and buy_avg_price == None and len(buys) < BUY_HAVE_COUNT:
                        print(">>>>> buy")
                        upbit.buy_market_order(market, BUY_UNIT_PRICE)
        except Exception as e:
            e