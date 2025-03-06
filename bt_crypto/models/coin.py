from sqlalchemy import Boolean,Column,String
from .base import Base

class Coin(Base):
    __tablename__="coins"
    symbol=Column(String,primary_key=True,unique=True)
    enabled=Column(Boolean)
    def __init__(self,symbol:str,primary_key=True):
        self.symbol=symbol
    def __add__(self,other):
        if isinstance(other,str):
            return self.symbol+other
        if isinstance(other,Coin):
            return self.symbol+other.symbol
        raise TypeError(f"unsupported type")
    def __repr__(self):
        return f"[{self.symbol}]"
