import backtrader as bt
import datetime
from bt_crypto.strategies.base import BaseStrategy
class Strategy(BaseStrategy):
    params = (
        ('fast', 12),
        ('slow', 26),
        ('signal', 9),
             )
    def __init__(self):
        super().__init__()
        self.sizer=bt.sizers.PercentSizer(percents=20)
        self.mome=(self.high_price-self.low_price)*self.volume
        self.macd=bt.indicators.MACD(
                self.mome,
                period_me1=self.p.fast,
                period_me2=self.p.slow,
                period_signal=self.p.signal,
                )
        self.crossover=bt.indicators.CrossOver(self.macd.macd,self.macd.signal)
    def next(self):
        if self.broker.getposition(self.data).size==0:
            if self.crossover[0] and self.close_price[0]-self.open_price[0] >0:
                self.buy(
                    size=self.broker.get_value()*self.p.position_to_balance/self.close_price[0]
                    )
            if self.crossover[0] and self.close_price[0]-self.open_price[0] <0:
                self.sell(
                    size=self.broker.get_value()*self.p.position_to_balance/self.close_price[0]
                    )

        else:
                if self.crossover[0]:
                    self.close()
