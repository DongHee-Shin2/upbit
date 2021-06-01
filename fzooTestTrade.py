import time
import pyupbit
import datetime

access = "accesskey"
secret = "secretkey"

sel_up_per = 1.1
plus_buy_per = -5 # 추가매수 기준 손실율
buy_lock = False # 종목매수 막기
all_sale = False # 일괄매도
# all_sale = True # 일괄매도
buy_ticker_count = 20 # 보유 종목수
buy_type = "515" # 매매법 515, 112224
# buy_type = "112224" # 매매법 515, 112224
buy_unit_price = 6000


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
        try:
            market = target['market']
            if market.find('KRW') != -1:

                now = datetime.datetime.now()
                start_time = get_start_time(market)
                end_time = start_time + datetime.timedelta(days=1)
                # print(start_time)
                # print(end_time)
                # print(now)
                print(market)
                current_price = get_current_price(market)
                print(current_price)
                buy_avg_price = get_avg_buy_price(market)
                print(buy_avg_price)
                # 보유 종목 매도
                if buy_avg_price != None:
                    print(">>>>>>>>>>>>>>>>>")
                    upper = get_up_per(market)
                    print(upper)
                    # 익절
                    if (all_sale == True or upper > sel_up_per) and buy_type != "515":
                        print(">>>>>>>>>>> sale")
                        btc_balance = upbit.get_balance(market)
                        upbit.sell_market_order(market, btc_balance)
                    # 추가 매수(물타기)
                    if all_sale == False and upper < plus_buy_per:
                        krw = get_balance("KRW")
                        if krw > 10000:
                            upbit.buy_market_order(market, 10000)
                    # 5이평 15이평 돌파 매매시 5이평이 15이평을 깨면 매도
                    if all_sale == False and buy_type == "515":
                        # ma5 = get_ma_price(market,5)
                        ma15 = get_ma_price(market,15)
                        print("515 sale check")
                        print(ma15)
                        print(current_price)
                        if current_price < ma15:
                            print(">>>>>>>>>>> 515 sale")
                            btc_balance = upbit.get_balance(market)
                            upbit.sell_market_order(market, btc_balance)



                if start_time < now < end_time - datetime.timedelta(seconds=10):
                    # 112, 224 이평 근처 (5%)
                    if buy_type == "112224":
                        # target_price = get_target_price(market, 0.5)
                        ma112 = get_ma_price(market,112)
                        ma224 = get_ma_price(market,224)
                        if isNaN(ma112):
                            ma112 = 0
                        if isNaN(ma224):
                            ma224 = 0
                        ma112_gap_per = get_gap_up_per(current_price,ma112)
                        ma224_gap_per = get_gap_up_per(current_price,ma224)
                        if (ma112_gap_per > 0 and ma112_gap_per < 5) or (ma224_gap_per > 0 and ma224_gap_per < 5):
                        # print(target_price)
                        # if target_price < current_price:
                            krw = get_balance("KRW")
                            if krw > buy_unit_price:
                                tickers = get_buy_list()
                                if all_sale == False and len(tickers) < buy_ticker_count and buy_avg_price == None and buy_lock == False:
                                    print(">>>>>>>>>>> buy")
                                    upbit.buy_market_order(market, buy_unit_price)

                    # 5이평 15이평 돌파
                    if buy_type == "515":
                        ma5 = get_ma_price(market,5)
                        pma5 = get_yday_ma_price(market,5)
                        ma15 = get_ma_price(market,15)
                        pma15 = get_yday_ma_price(market,15)
                        if pma15 > pma5 and ma15 < ma5 and current_price > ma15:
                            krw = get_balance("KRW")
                            if krw > buy_unit_price:
                                tickers = get_buy_list()
                                if all_sale == False and len(tickers) < buy_ticker_count and buy_avg_price == None and buy_lock == False:
                                    print(">>>>>>>>>>> buy")
                                    upbit.buy_market_order(market, buy_unit_price)
                                          
                # else:
                #     btc = get_balance("BTC")
                #     if btc > 0.00008:
                #         upbit.sell_market_order(market, btc*0.9995)

                # time.sleep(1)

            if buy_type != "515":
                print(sell_count)
                if sell_count > 5:
                    sell_count = 0
                    tickers = get_buy_list()
                    # 보유종목
                    for ticker in tickers:
                        market = ticker['unit_currency'] + "-" + ticker['currency']
                        current_price = get_current_price(market)
                        buy_avg_price = get_avg_buy_price(market)
                        if buy_avg_price != None:
                            upper = get_up_per(market)
                            print(market)
                            print(upper)
                            # 익절
                            if (all_sale == True or upper > sel_up_per) and buy_type != "515":
                                print(">>>>>>>>>>> sale")
                                btc_balance = upbit.get_balance(market)
                                upbit.sell_market_order(market, btc_balance)
                            # 추가 매수(물타기)
                            if all_sale == False and upper < plus_buy_per:
                                krw = get_balance("KRW")
                                if krw > 10000:
                                    upbit.buy_market_order(market, 10000)
                            # 5이평 15이평 돌파 매매시 5이평이 15이평을 깨면 매도
                            if all_sale == False and buy_type == "515":
                                # ma5 = get_ma_price(market,5)
                                ma15 = get_ma_price(market,15)
                                if current_price < ma15:
                                    print(">>>>>>>>>>> 515 sale")
                                    btc_balance = upbit.get_balance(market)
                                    upbit.sell_market_order(market, btc_balance)

                else:
                    sell_count = sell_count + 1
        except Exception as e:
            e