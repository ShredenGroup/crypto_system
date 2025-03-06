import backtrader as bt
from datetime import datetime
from bt_crypto.strategies.base import BaseStrategy
class Strategy(BaseStrategy):
    params=(
        ('period',20),
        ('devfac',2),
        ('stop_loss_ATR',2),
        ('profit_multi',2)
)
    def __init__(self):
        super().__init__()
        self.ATR = bt.indicators.ATR()
        self.bollinger=bt.indicators.BollingerBands(
                self.close_price(0),
                period=self.p.period,
                devfactor=self.p.devfac
        )
        self.top=self.bollinger.top
        self.bottom=self.bollinger.bot
        self.middle=self.bollinger.mid
        self.hold_position=False
        self.order=None
        self.count=0
        self.rsi=bt.indicators.RSI()
    def notify_order(self,order):
        if order.status is not bt.Order.Completed:
            return
        if not self.position:
            return
        if order.isbuy():
            print('order filled')
            sell.sell(exectype=bt.Order.stop,
    def next(self):
        if self.position.size != 0:
            return
        if self.close_price[-1] > self.top[-1] and self.close_price[0] < self.top[-1]:
            self.order=self.buy(size=self.broker.getvalue()*self.p.position_to_balance/self.close_price[0])
#        if self.close_price[-1] < self.bottom[-1] and self.close_price[0] > self.bottom[0]:
#            self.order=self.sell(size=self.broker.getvalue()*self.p.position_to_balance/self.close_price[0])

