from sqlalchemy import Boolean,Column,String,Integer,Enum,ForeignKey,Float,BigInteger
from sqlalchemy.orm import relationship
from .base import Base
import enum
class OrderState(enum.Enum):
    NEW="NEW"
    PARTIALLY_FILLED="PARTIALLY_FILLED"
    FILLED="FILLED"
    CANCELED="CANCELED"
    REJECTED="REJECTED"
    EXPIRED="EXPIRED"
    EXPIRED_IN_MATCH="EXPIRED_IN_MATCH"
class Direction(enum.Enum):
    LONG="LONG"
    SHORT="SHORT"
class Side(enum.Enum):
    BUY="BUY"
    SELL="SELL"
class Order(Base):
    __tablename__="order"
    order_id=Column(Integer,primary_key=True,unique=True)
    order_coin_id=Column(String,ForeignKey("coins.symbol"))
    order_coin=relationship("Coin",foreign_keys=[order_coin_id],lazy="joined")
    amount=Column(Float,nullable=False)
    order_state=Column(Enum(OrderState))
    place_time=Column(BigInteger)
    side=Column(Enum(Side))
    def __init__(self,order_id:int,order_coin_id:str,amount:float,order_state:OrderState,place_time:int,side:str):
        self.order_id=order_id
        self.order_coin_id=order_coin_id
        self.amount=amount
        self.order_state=order_state
        self.place_time=place_time
        self.side=side 
    def info(self):
        print(self.order_id)
    def get_id(self):
        return self.order_id
    def get_symbol(self):
        return self.order_coin_id
