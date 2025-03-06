from .db import DataBase
from .logger import Logger
from typing import List,Dict,Optional
from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient
from binance.um_futures import UMFutures
import pandas as pd
from .config import Config
from datetime import datetime,timedelta
from enum import Enum
from .utils import load_configs
from threading import Thread
class Side(Enum):
    BUY:str='BUY'
    SELL:str='SELL'
class ApiManager():
    def __init__(self,config:Config,db:DataBase):
        self.client=UMFutures(key=config.API_KEY,private_key=config.API_SECRET)
        self.bt_config=load_configs()
        self.logger=Logger('api')
        self.db=db
    def get_kline(self,symbol:str,interval:str,start_time:str=None,end_time:str=None)->pd.DataFrame:	
        start_ms=None
        end_ms=None
        if start_time:
            if not self.bt_config.get_basic_setting()['livetrade']:
                start_ms=int(datetime.strptime(start_time,"%Y%m%d").timestamp()*1000)
            else:
                current_ms=int(datetime.utcnow().timestamp()*1000)
                time_multiplier=1
                if self.bt_config.get_pair_config(symbol)['interval']=='5m':
                    time_multiplier=5
                if self.bt_config.get_pair_config(symbol)['interval']=='1d':
                    time_multiplier=1440
                if self.bt_config.get_pair_config(symbol)['interval']=='1h':
                    time_multiplier=60
                if self.bt_config.get_pair_config(symbol)['interval']=='4h':
                    time_multiplier=240
                start_ms=int((datetime.utcnow()-timedelta(minutes=40*time_multiplier)).timestamp()*1000)
        if end_time:
            if not self.bt_config.get_basic_setting()['livetrade']:
                end_ms=int(datetime.strptime(end_time,"%Y%m%d").timestamp()*1000)
        result=self.client.klines(symbol=symbol,
        interval=interval,
        startTime=start_ms if start_time is not None else None,
        endTime=end_ms if end_time is not None else None,
        limit=1500)
        df=pd.DataFrame(result)
        df=df.iloc[:,0:6]
        df[0]=pd.to_datetime(df[0],unit='ms')
        for col in [1,2,3,4,5]:
            df[col]=df[col].astype(float)
        df=df.rename(columns={0:"datetime",1:"open",2:"high",3:"low",4:"close",5:"volume"}).set_index('datetime')
        return df
    def place_order(self,symbol:str,side:Side,order_type:str,quantity:float,price:float=None,**args)->str:
        order_params={
                "symbol":symbol,
                "side":side.value,
                "quantity":quantity,
                "type":order_type,
                **args
                }
        if order_type!='MARKET':
            if price is None:
                raise ValueError('Price should be a valid value')
            order_params['price']=price
        response=self.client.new_order(**order_params)
        self.db.add_order(
            order_id=response['orderId'],
            symbol=response['symbol'],
            amount=response['origQty'],
            order_state='FILLED' if order_type=='MARKET' else response['status'],
            place_time=response['updateTime'],
            side=response['side']
            )
        print(response)
        return response
    def close_all_positions(self):
        positions_amount={}
        all_open_positions:List[Dict]=self.get_open_positions()
        for position in all_open_positions:
            symbol=position['symbol']
            amount=float(position['positionAmt'])
            self.place_order(symbol=symbol,side=Side.BUY  if amount<0 else Side.SELL,order_type='MARKET',quantity=amount)
    def close_certain_position(self,symbol:str):
        if self.get_certain_position(symbol) is None:
            print('you dont have any position')
            return False
        amount=float(self.get_certain_position(symbol))
        bid_price=self.get_bid_price(symbol)
        ask_price=self.get_bid_price(symbol,direction='asks')
        result={}
        while not result:
            result=self.place_order(
                    symbol=symbol,
                    side=Side.BUY  if amount<0 else Side.SELL,
                    order_type='Limit',
                    quantity=abs(amount),
                    reduceOnly='true',
                    timeInForce='GTC',
                    price=bid_price if amount<0 else ask_price)
        return True
    def close_then_place(self,symbol:str,side:Side,order_type:str,quantity:float,price:float=None,**kwargs)->str:
        live_orders= self.db.get_live_orders()
        if live_orders:
            print('you have open orders, return')
            return
        position=self.get_certain_position(symbol)
        result={}
        if position is None:
            print('No position close, put order directly')
            result=self.place_order(symbol=symbol,side=side,order_type=order_type,quantity=quantity,price=price,**kwargs)
        else:
            if position > 0 and side==Side.BUY:
                print('you have already hold long position')
                return
            if position>0 and side==Side.SELL:
                result=self.place_order(symbol=symbol,side=side,order_type=order_type,quantity=quantity+position,price=price,**kwargs)
            if position < 0 and side==Side.SELL:
                print('You have already hold short position')
                return 
            if position <0 and side==Side.BUY:
                result=self.place_order(symbol=symbol,side=side,order_type=order_type,quantity=quantity+abs(position),price=price,**kwargs)
        return result
    def get_open_positions(self)->List[Dict]:
        account_info=self.client.account()
        return account_info['positions']
    def get_certain_position(self,symbol:str)->float:
        all_positions=self.get_open_positions()
        for position in all_positions:
            if position['symbol']==symbol:
                return position[positionAmt]
        return None
    def get_certain_position(self,symbol:str)->Optional[Dict]:
        positions=self.get_open_positions()
        for position in positions:
            if position['symbol'] ==symbol:
                return float(position['positionAmt'])
        else:
            print(f'No position for {symbol}')
            return None
    def get_balance(self)->float:
        balance=float(self.client.account()['totalWalletBalance'])
        return balance
    def cancel_order(self,symbol:str):
        #This is the function cancelling order for specific symbol
        response=self.client.cancel_open_orders(symbol)
        if response is not None:
            for order in self.db.get_live_orders():
                orderId=order['orderId']
                self.db.update_order(order_id=orderId,order_state='CANCELED')
            self.logger.info('Live orders canceled')
        return response
    def cancel_order_id(self,symbol:str,orderId):
        result=self.client.cancel_order(
                symbol=symbol,
                orderId=orderId
        )
        self.db.del_order(order_id=orderId)
    def get_bid_price(self,symbol,limit:int=5,direction:str='bids'):
        response=self.client.depth(symbol=symbol,limit=limit)
        result=response[direction][0][0]
        return result
    def get_current_order(self,db:DataBase,symbol:str=None):
        response=self.client.get_orders() 
        print(response)
    def get_order(self,orderId:int,symbol:str):
        result=self.client.query_order(symbol,orderId=orderId)
        return result
    def get_open_orders(self,symbol:str):
        result=self.client.get_open_orders(symbol)
        return result
    def modify_order(self,symbol,side,orderId,price,quantity,**kwargs):
        result=self.client.modify_order(symbol=symbol,side=side,orderId=orderId,price=price,quantity=quantity,**kwargs)
        return result
    def order_checker(self):
        orders=self.db.get_live_orders()
        results=[self.get_order(order['orderId'],order['symbol']) for order in orders]
        for result in results:
            if result['status'] not in ['NEW','PARTIALLY_FILLED']:
                self.db.update_order(order_id=result['orderId'],order_state=result['status'])
    def order_chaser(self,symbol=str,executed_time:int=0,event=None):
        try:
            """
            Get live order from database and ensure they are still unfilled by fetching latest status from biancne server
            Then executed them in certain period
            """ 
            self.order_checker()
            orders = self.db.get_live_orders()
            results=[self.get_order(order['orderId'],order['symbol']) for order in orders]
            if not results:
                print('No live order detected')
                return
            sample_result=results[0]
            order_status=sample_result['status']
            if order_status not in['NEW','PARTIALLY_FILLED']:
                print('Orders have been fully executed or canceled')
                return
            order_time=sample_result['time']
            order_time_sec=int(sample_result['time']/1000)
            timestamp_now=int(datetime.now().timestamp())
            limit_time=order_time_sec+executed_time
            left_time=limit_time-timestamp_now
            bid_price=float(self.get_bid_price(sample_result['symbol']))
            ask_price=float(self.get_bid_price(sample_result['symbol'],5,'asks'))
            lag_1=order_time_sec+int(executed_time/2)
            lag_2=order_time_sec+int(executed_time/8*7)
#            dt_1=datetime.fromtimestamp(lag_1)
#            dt_2=datetime.fromtimestamp(lag_2)
#            print(dt_1)
#            print(dt_2)
#            return
            if left_time<=0:
                print('This order is out of executed_time,cancel operation executed')
                self.cancel_order_id(symbol,sample_result['orderId'])
                return
            if timestamp_now<=lag_1:
                print('Just wait placed order to be executed')
            elif timestamp_now > lag_1 and timestamp_now<=lag_2:
                print('now modify order to bid price')
                result=self.modify_order(symbol=sample_result['symbol'],side=sample_result['side'],orderId=sample_result['orderId'],price=bid_price,quantity=float(sample_result['origQty'])-float(sample_result['executedQty']))
            else: 
                print('now modify order to ask price')
                result=self.modify_order(
                    symbol=sample_result['symbol'],
                    side=sample_result['side'],
                    orderId=sample_result['orderId'],
                    price=ask_price,quantity=float(sample_result['origQty'])-float(sample_result['executedQty']))
        except Exception as e:
            self.logger.error(f"获取订单时发生错误: {str(e)}")
            return []
    def votilation_caculator(self,interval,start,end):
       pass 

if __name__=='__main__':
    config=Config()
    logger=Logger('database')
    db=DataBase(logger)
    client=ApiManager(config,db)
    client.order_chaser(4000)
    #client.close_certain_position('DOGEUSDT')
    #client.place_order(symbol='DOGEUSDT',side=Side.SELL,order_type='LIMIT',
    #                   quantity=18,price =1,timeInForce='GTC')
    #print(client.order_checker())
    #client.modify_order(symbol='DOGEUSDT',side='SELL',orderId=61791031510,price=0.9,quantity=17)
    #db.del_db()
    #client.cancel_order('DOGEUSDT')
