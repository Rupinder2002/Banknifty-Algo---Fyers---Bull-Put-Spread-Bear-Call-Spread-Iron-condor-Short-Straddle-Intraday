from select import select
from datetime import datetime
from telnetlib import STATUS
import webbrowser
import telegram
from truedata_ws.websocket.TD import TD
from copy import deepcopy
import pandas as pd
from datetime import date
import time
import sys
from urllib import response  
from os.path import exists
import json
from fyers_api import fyersModel
from fyers_api import accessToken
import requests
class bot(object):
    def __init__(self) -> None:
        self.username           = 'true data api username'
        self.password           = 'true data api password'
        self.API_KEY            = 'api_key'
        self.realtime_port      = 8082
        self.client_id          =   'fyers api client ID'
        self.secret_key         =   'secret key'
        self.redirect_uri       =   'http://127.0.0.1:8080/algo/index.jsp'
        self.response_type      =   "code"
        self.grant_type         =   "authorization_code"
        self.intro              = 'Welcome to Trading Bot'
        self.auth_file          =  'D:/authcodes/authcode_'+datetime.now().strftime('%Y%m%d')+'.json'
        self.accessFile         =  'access_token_'+datetime.now().strftime('%Y%m%d')+'.json' 
        self.orderFile          = 'orders.json'
        self.app_id             = 16725540
        self.api_hash           = 'place your own api hash'
        self.bot_token          = 'place your own bot tokem'
        self.phone_no           = '917550278860'
        self.chat_id            =  0
        self.seconds            = 0
        self.expiry             = str(datetime.now().year)[2:]+str(datetime.now().month)+str(datetime.now().day+4)
        self.sendNotification('Bot Initialized...')

    def getWeekHLC(self):
        f = open('week_data.json')
        data = json.load(f)
        self.high   = data['high']
        self.low    = data['low']
        self.close  = data['close']

    def showProfile(self):
        return self.fyers.get_profile()

    def showPositions(self):
        return self.fyers.positions()

    def showFunds(self):
        return self.fyers.funds()

    def generateAuthCode(self):
        if exists(self.auth_file):
            f = open(self.auth_file)
            data = json.load(f)
            self.auth_token = data['auth_code']
            return self.auth_token   
        else:
            response = self.session.generate_authcode()
            webbrowser.open(response) 
            while True:
                print('Checking for Auth File')
                if exists(self.auth_file):
                    f = open(self.auth_file)
                    data = json.load(f)
                    self.auth_token = data['auth_code']
                    return self.auth_token   
                else:
                    time.sleep(3)
                    print('Waiting for auth file generation')
        
    def generateAccessToken(self):
        if exists(self.auth_file) and not exists(self.accessFile):
            auth_code = self.generateAuthCode()
            self.session.set_token(auth_code)
            response = self.session.generate_token()
            self.access_token = response['access_token']
            data = {'access_token':self.access_token}
            with open(self.accessFile,'w',encoding='utf-8') as f:
                json.dump(data,f,ensure_ascii=False,indent=4)
            return self.access_token
        elif exists(self.accessFile):
            f = open(self.accessFile)
            data = json.load(f)
            self.access_token = data['access_token']
            return self.access_token
        
    def initFyers(self):
        self.sendNotification('Creating Fyers Model....')
        self.session = accessToken.SessionModel(
                client_id       =   self.client_id,
                secret_key      =   self.secret_key,
                redirect_uri    =   self.redirect_uri,
                response_type   =   self.response_type,
                grant_type      =   self.grant_type
                )
        auth_code       = self.generateAuthCode()
        access_token    = self.generateAccessToken()
        self.fyers      = fyersModel.FyersModel(client_id=self.client_id token=access_token)
        self.is_async = True  

    def recordHLC(self,hlc):
        data = {'high':float(hlc[0]),'low':float(hlc[1]),'close':float(hlc[2])}
        with open('week_data.json','w',encoding='utf-8') as f:
                json.dump(data,f,ensure_ascii=False,indent=4)
        print('Recorded')


    def fetchOrderDetails(self):
        strikes = []
        prices  = []
        f = open('orders.json')
        data = json.load(f)
        for key in data.keys():
            if data[key]['status'] == 'Live':
                strikes = data[key]['strikes']
                prices  = data[key]['avg_price']
                status  = 'Live'
                break
            else:
                status = 'Finished'
        return (strikes,prices,status)        

    def initMarketFeed(self,type):
        self.sendNotification('Connecting to Market...')
        td_app      = TD(self.username,self.password,live_port = self.realtime_port,historical_api=False)
        symbols     = []
        avg_prices  = []
        if type==1:
            symbols,avg_prices,status = self.fetchOrderDetails()
        elif type==2 or type==3:
            symbols = ['NIFTY BANK']
        live_data_objs = {}
        req_ids = td_app.start_live_data(symbols)
        print(req_ids)
        time.sleep(1)
        for req_id in req_ids:
            live_data_objs[req_id] = deepcopy(td_app.live_data[req_id])
            #print(f'touchlinedata -> {td_app.touchline_data[req_id]}')
        while True:
            ltp = []
            self.seconds = self.seconds+1
            print(self.seconds)
            #print(symbols)
            #print(avg_prices)
            time.sleep(3)
            for req_id in req_ids:
                if   td_app.live_data[req_id] == live_data_objs[req_id]:
                    ltp.append(td_app.live_data[req_id].ltp)
                    #print(f'{td_app.live_data[req_id].symbol} > {td_app.live_data[req_id].ltp} > {td_app.live_data[req_id].change:.2f}')
                    live_data_objs[req_id] = deepcopy(td_app.live_data[req_id])
            print(ltp)
            if len(ltp)==2 and type==1:
                lot_size = 500
                buy_value = (float(ltp[0])-avg_prices[0])*lot_size
                sell_value = (avg_prices[1]-float(ltp[1]))*lot_size
                current_position = round(sell_value+buy_value,2)
                print('Current Options Positions:{0}'.format(current_position))
                if(current_position>=17000):
                    self.sendNotification('Current Profit is {0}'.format(current_position))
                    self.sendNotification('Exit the Positions')
                    f    = open('orders.json')
                    data = json.load(f)
                    for key in data.keys():
                        if data[key]['status'] == 'Live':
                            data[key]['status']  = 'Finished'
                            with open(self.orderFile,'w',encoding='utf-8') as f:
                                json.dump(data,f,ensure_ascii=False,indent=4)
                    f.close()
                else:
                    time.sleep(30)
                    self.sendNotification('Current Profit is {0}'.format(current_position))
            elif type==2:
                if self.seconds == 3601:
                    decision = self.selectionCriteria(ltp[0])
                    self.PlaceOrder(decision)
                else:
                    pass
            elif type==3:
                if self.seconds == 3:
                    self.intradayStrategy(ltp[0])
                
                
    def sendNotification(self,msg):
        algobot = telegram.Bot(token=self.bot_token)
        algobot.sendMessage(chat_id=self.chat_id,text=msg)

    def monitorTrade(self):
        print('Analysing Orders.............')
        time.sleep(3)
        print('Fetching Market Feed..........')
        self.initMarketFeed()

    def prepareOrder(self,symbol,type,price,productType):
        data = {}
        if type=="B":
         data = {
                    "symbol"        :symbol,
                    "qty"           : 25,
                    "type"          : 2,
                    "side"          : 1,
                    "productType"   : "MARGIN" ,
                    "limitPrice"    : 0,
                    "stopPrice"    : 0,
                    "validity"      : "DAY",
                    "disclosedQty"  : 0,
                    "offlineOrder"  : "False",
                    "stopLoss"      : 0,
                    "takeProfit"    : 0
                }
        elif type=='S':
            data={
                    "symbol"        :symbol,
                    "qty"           : 25,
                    "type"          : 2,
                    "side"          : -1,
                    "productType"   : "MARGIN" ,
                    "limitPrice"    : 0,
                    "stopPrice"    : 0,
                    "validity"      : "DAY",
                    "disclosedQty"  : 0,
                    "offlineOrder"  : "False",
                    "stopLoss"      : 0,
                    "takeProfit"    : 0
                }
        elif type=='SL':
             data={
                    "symbol"        :symbol,
                    "qty"           : 25,
                    "type"          : 4,
                    "side"          : 1,
                    "productType"   : "INTRADAY" ,
                    "limitPrice"    : price+0.5,
                    "stopPrice"     : price,
                    "validity"      : "DAY",
                    "disclosedQty"  : 0,
                    "offlineOrder"  : "False",
                    "stopLoss"      : 0,
                    "takeProfit"    : 0
                }
        return data

    def fetchExecutionPrices(self,order_id):
        prices = []
        trades = self.fyers.tradebook()
        for trade in trades['tradeBook']:
            for order in order_id:
                if trade['orderNumber'] == order:
                    prices.append(trade['tradePrice'])
                else:
                    pass
        return prices

    def monitorIntraday(self):
        while True:
            positions   = self.fyers.positions()
            realised    = positions['overall']['pl_realized']
            print(realised)
            if realised< 0 :
                self.sendNotification('We will try tomorrow,just relax and be calm.')
                break
            elif realised > 0:
                self.sendNotification('Hurray! Intraday Equity Profit but dont get greedy,follow the rules.')
                break
            time.sleep(30)


    def PlaceOrder(self,selection): 
            data = {}
            order_id    = []
            strikes     = []
            prices      = []
            if selection['type'] == 0  :
                buy_order   = self.prepareOrder("NSE:BANKNIFTY"+self.expiry+str(selection['put_buy_price'])+'PE','B',0,'MARGIN')
                sell_order  = self.prepareOrder("NSE:BANKNIFTY"+self.expiry+str(selection['put_sell_price'])+'PE','S',0,'MARGIN')
                buy_data    = self.fyers.place_order(buy_order)
                sell_data   = self.fyers.place_order(sell_order)
                print(buy_order)
                print(sell_order)
                if buy_data['s'] == 'ok' and sell_data['s'] == 'ok':
                    self.sendNotification('Put Buy  Order Status: {0}'.format(buy_data['message']))
                    self.sendNotification('Put Sell Order Status: {0}'.format(sell_data['message']))
                    entry_date = datetime.now().strftime('%Y%m%d')
                    order_id.append(buy_data['id'])
                    order_id.append(sell_data['id'])
                    strikes.append(selection['put_buy_price'])
                    strikes.append(selection['put_sell_price'])
                    prices = self.fetchExecutionPrices(order_id)
                    data[entry_date]['id_s'] = order_id
                    data['strikes'] = strikes
                    data['avg_price'] = prices
                    with open(self.orderFile,'w',encoding='utf-8') as f:
                        json.dump(data,f,ensure_ascii=False,indent=4)
                else:
                     self.sendNotification('Put Buy  Order Status: {0}'.format(buy_data['message']))
            elif selection['type'] == 1 :
                buy_order   = self.prepareOrder("NSE:BANKNIFTY"+self.expiry+str(selection['call_buy_price'])+'CE','B',0,'MARGIN')
                sell_order  = self.prepareOrder("NSE:BANKNIFTY"+self.expiry+str(selection['call_sell_price'])+'CE','S',0,'MARGIN')
                buy_data    = self.fyers.place_order(buy_order)
                sell_data   = self.fyers.place_order(sell_order)
                print(buy_order)
                print(sell_order)
                if buy_data['s'] == 'ok' and sell_data['s'] == 'ok':
                        self.sendNotification('Call Buy  Order Status: {0}'.format(buy_data['message']))
                        self.sendNotification('Call Sell Order Status: {0}'.format(sell_data['message']))
                        entry_date = datetime.now().strftime('%Y%m%d')
                        order_id.append(buy_data['id'])
                        order_id.append(sell_data['id'])
                        strikes.append(selection['call_buy_price'])
                        strikes.append(selection['call_sell_price'])
                        prices = self.fetchExecutionPrices(order_id)
                        data[entry_date]['id_s'] = order_id
                        data['strikes'] = strikes
                        data['avg_price'] = prices
                        with open(self.orderFile,'w',encoding='utf-8') as f:
                            json.dump(data,f,ensure_ascii=False,indent=4)
                else:
                    self.sendNotification('Put Buy  Order Status: {0}'.format(buy_data['message']))

            elif selection['type'] == 3 :
                buy_order_1   = self.prepareOrder("NSE:BANKNIFTY"+self.expiry+str(selection['put_buy_price'])+'PE','B',0,'MARGIN')
                buy_order_2  = self.prepareOrder("NSE:BANKNIFTY"+self.expiry+str(selection['call_buy_price'])+'CE','B',0,'MARGIN')
                leg_1_buy = self.fyers.place_order(buy_order_1)
                leg_2_buy = self.fyers.place_order(buy_order_2)
                sell_order_1   = self.prepareOrder("NSE:BANKNIFTY"+self.expiry+str(selection['put_sell_price'])+'PE','S',0,'MARGIN')
                sell_order_2  = self.prepareOrder("NSE:BANKNIFTY"+self.expiry+str(selection['call_sell_price'])+'CE','S',0,'MARGIN')
                leg_1_sell = self.fyers.place_order(sell_order_1)
                leg_2_sell = self.fyers.place_order(sell_order_2)

                if leg_1_buy['s']=='ok' and leg_2_buy['s']=='ok' and leg_1_sell['s']=='ok' and leg_2_sell['s']=='ok':
                    self.sendNotification('Put  Buy Order Status:   {0}'.format(leg_1_buy['message']))
                    self.sendNotification('Call Buy Order Status:   {0}'.format(leg_2_buy['message']))
                    self.sendNotification('Put  Sell Order Status:  {0}'.format(leg_1_sell['message']))
                    self.sendNotification('Call Sell Order Status:  {0}'.format(leg_2_sell['message']))
                    entry_date = datetime.now().strftime('%Y%m%d')
                    order_id.append(leg_1_buy['id'])
                    order_id.append(leg_2_buy['id'])
                    order_id.append(leg_1_sell['id'])
                    order_id.append(leg_2_sell['id'])
                    strikes.append(selection['put_buy_price'])
                    strikes.append(selection['call_buy_price'])
                    strikes.append(selection['put_sell_price'])
                    strikes.append(selection['call_sell_price'])
                    prices = self.fetchExecutionPrices(order_id)
                    data[entry_date]['id_s'] = order_id
                    data['strikes'] = strikes
                    data['avg_price'] = prices
                    with open(self.orderFile,'w',encoding='utf-8') as f:
                        json.dump(data,f,ensure_ascii=False,indent=4)


    def intradayStrategy(self,ltp):
        order_id = []
        self.sendNotification('Finding The strike Price....')
        strike_price = int(round((ltp),-2))
        ce_sell_order  = self.prepareOrder("NSE:BANKNIFTY"+self.expiry+str(strike_price)+'CE','S',0,'INTRADAY')
        pe_sell_order  = self.prepareOrder("NSE:BANKNIFTY"+self.expiry+str(strike_price)+'CE','S',0,'INTRADAY')
        sell_ce_data    = self.fyers.place_order(ce_sell_order)
        sell_pe_data    = self.fyers.place_order(pe_sell_order)
        print(sell_ce_data)
        print(sell_pe_data)
        order_id.append(sell_ce_data['id'])
        order_id.append(sell_pe_data['id'])
        self.sendNotification('Intraday Short Straddle Created with Strike Price of '+str(strike_price))
        if sell_ce_data['s'] == 'ok' and sell_pe_data['s'] == 'ok':
            self.sendNotification('Intraday Short Straddle Created with Strike Price of '+str(strike_price))
            prices          = self.fetchExecutionPrices(order_id)
            ce_traded_price = prices[0]
            pe_traded_price = prices[1]
            ce_sl_price     = prices[0]+round(ce_traded_price*2)/2
            pe_sl_price     = prices[1]+round(pe_traded_price*2)/2
            ce_sell_order   = self.prepareOrder("NSE:BANKNIFTY"+self.expiry+str(strike_price)+'CE','SL',ce_sl_price,'INTRADAY')
            pe_sell_order   = self.prepareOrder("NSE:BANKNIFTY"+self.expiry+str(strike_price)+'PE','SL',pe_sl_price,'INTRADAY')
            ce_sl_data      = self.fyers.place_order(ce_sell_order)
            pe_sl_data    = self.fyers.place_order(pe_sell_order)
            print(ce_sl_data)
            print(pe_sl_data)
            if ce_sl_data['s'] == 'ok' and pe_sl_data['s']=='ok':
                self.sendNotification('SL Orders places for both the legs')
        elif sell_ce_data['s']=='error' and sell_pe_data['s']=='error':
            self.sendNotification('Error placing short straddle order: '+sell_ce_data['message'])


    def selectionCriteria(self,ltp):
        self.sendNotification('Finding the right Strategy and Strike Prices......')
        pp      = float(str(round((self.high+self.low+self.close)/3,2)))
        line_1      = float(str(round((self.high+self.low)/2,2)))
        line_2     = round((pp-line_1)+pp,2)
        if line_1 > line_2:
            tc = line_1
            bc = line_2
        else:
            tc = line_2
            bc = line_1
        print('Pivot: {0},TC: {1},BC: {2}'.format(pp,tc,bc))

        sell_strike_price   = 0
        buy_strike_price    = 0
        upper_twin_high     = 0.00
        upper_twin_low      = 0.00
        r1 = round((2 * pp ) - self.low,2)
        s1 = round((2 * pp ) - self.high,2)
        print('r1: '+str(r1))
        print('s1: '+str(s1))
        if r1 >  self.high :
            upper_twin_high = r1
            upper_twin_low  = self.high 
        elif r1 < self.high:
            upper_twin_high = self.high
            upper_twin_low  = r1

        if s1 < self.low:
            lower_twin_low  = s1
            lower_twin_high = self.low
        elif s1 > self.low:
            lower_twin_low  = self.low
            lower_twin_high = s1

        close                   =   ltp
        print('upper twin low: '+str(upper_twin_low))
        print('lower_twin_high: '+str(lower_twin_high))

        if (close > tc and close< upper_twin_low):
            sell_strike_price   = int(round((bc+lower_twin_low)/2,-2))
            buy_strike_price    = sell_strike_price - 300
            data = {'type':0,'put_sell_price':sell_strike_price,'put_buy_price':buy_strike_price}
            msg = "Bull Put Spread,Sell: "+str(sell_strike_price)+" PE,Buy: "+str(buy_strike_price)+"PE "
            self.sendNotification(msg)
            return data
            #print('Initiating Bull Put Spread, Selling PE at Strike Price of {0},Buying PE at Strike Price of {1}'.format(sell_strike_price,buy_strike_price))
        elif (close > tc and close > upper_twin_low):
            sell_strike_price   = int(round((bc),-2))
            buy_strike_price    = sell_strike_price - 300
            data = {'type':0,'put_sell_price':sell_strike_price,'put_buy_price':buy_strike_price}
            msg = "Bull Put Spread,Sell: "+str(sell_strike_price)+" PE,Buy: "+str(buy_strike_price)+"PE "
            self.sendNotification(msg)
            return data
            #print('Initiating Bull Put Spread, Selling PE at Strike Price of {0},Buying PE at Strike Price of {1}'.format(sell_strike_price,buy_strike_price))
        elif (close < bc and close > lower_twin_high):
            sell_strike_price   = int(round((tc+upper_twin_high)/2,-2))
            buy_strike_price    = sell_strike_price + 300
            data = {'type':1,'call_sell_price':sell_strike_price,'call_buy_price':buy_strike_price}
            msg = "Bear Call Spread,Sell: "+str(sell_strike_price)+" CE,Buy: "+str(buy_strike_price)+"CE "
            self.sendNotification(msg)
            return data
            #print('Initiating Bear Call Spread, Selling CE at Strike Price of {0},Buying CE at Strike Price of {1}'.format(sell_strike_price,buy_strike_price))
        elif (close < bc and close < lower_twin_high):
            sell_strike_price   = int(round((tc),-2))
            buy_strike_price    = sell_strike_price + 300
            data = {'type':1,'call_sell_price':sell_strike_price,'call_buy_price':buy_strike_price}
            msg = "Bear Call Spread,Sell: "+str(sell_strike_price)+" CE,Buy: "+str(buy_strike_price)+"CE "
            self.sendNotification(msg)
            return data
            #print('Initiating Bear Call Spread, Selling CE at Strike Price of {0},Buying CE at Strike Price of {1}'.format(sell_strike_price,buy_strike_price))
        elif close > bc and close < tc:
            basic_strike_price  = int(round(close,-2))
            call_sell_price     = basic_strike_price + 1000
            call_buy_price      = call_sell_price + 300
            put_sell_price      = basic_strike_price - 1000
            put_buy_price       = put_sell_price - 300
            data = {'type':3,'put_sell_price':put_sell_price,'put_buy_price':put_buy_price,'call_sell_price':call_sell_price,'call_buy_price':call_buy_price}
            msg = "Iron Condor,Sell: "+str(put_sell_price)+" PE,Buy: "+str(put_buy_price)+" PE ,Sell: "+str(call_sell_price)+" CE,buy: "+str(call_buy_price)+" CE"
            self.sendNotification(msg)
            return data
            #print('Initiating Iron Condor,Sell Call at {0},buy Call at {1},Sell Put at {2},Buy Put at {3}'.format(call_sell_price,call_buy_price,put_sell_price,put_buy_price))
