from typing import List,Dict
from .models import Coin,Order,Base,OrderState
from typing import List,Optional
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship,sessionmaker,Session
from sqlalchemy import create_engine,String,MetaData,Table,or_
from .logger import Logger
from contextlib import contextmanager
from threading import Thread
import time
class DataBase:
    def __init__(self, logger: Logger, url="sqlite:///data/live_trading.db"):
        self.logger = logger
        self.engine=create_engine(url)
        self.SessionMaker=sessionmaker(bind=self.engine)
    def create_database(self):
        Base.metadata.create_all(self.engine)
    @contextmanager
    def db_session(self):
       session:Session=self.SessionMaker()
       yield session
       session.commit()
       session.close()
    def add_coin(self,symbol:str):
        with self.db_session() as session:
            existing_coin=session.query(Coin).filter_by(symbol=symbol).first()
            if existing_coin is None:
                coin=Coin(symbol)
                session.add(coin)
            else:
                self.logger.warning('Coin has already been in db')
    def add_order(self,order_id:int,symbol:str,amount:float,order_state:str,place_time:int,side:str):
        with self.db_session() as session:
            new_order = Order(order_id=order_id,
                              order_coin_id=symbol,
                              amount=amount,
                              place_time=place_time,
                              order_state=order_state,
                              side=side
                              )
            session.add(new_order)
            self.logger.info(f'New order added to database,order_id={order_id}')
    def del_order(self,order_id:int):
        with self.db_session() as session:
            order=session.get(Order,order_id)
            if order:
                session.delete(order)
                self.logger.info(f'Order {order_id} has been deleted')
            else:
                self.logger.warning(f'Order {order_id} is not found')
    def update_order(self,order_id:int,**kwg):
        with self.db_session() as session:
            order=session.get(Order,order_id)
            if order:
                for key,value in kwg.items():
                    if hasattr(order,key):
                        setattr(order,key,value)
            self.logger.info(f'order {order_id} updated')
    def del_db(self)->List[Dict]:
        Base.metadata.drop_all(self.engine)
        print('Database has already been removed')
    def get_live_orders(self):
        with self.db_session() as session:
            orders=session.query(Order).filter(or_(Order.order_state=='NEW',
                                                   Order.order_state== 'PARTIALLY_FILLED'))
            
            result=[{'symbol':order.order_coin_id,'orderId':order.order_id} for order in orders]
            return result
if __name__=="__main__":
    logger=Logger('database')
    db=DataBase(logger)
    db.create_database()
    db.add_coin('DOGEUSDT')
    db.get_live_orders()
