import backtrader as bt
from bt_crypto.strategies.base import BaseStrategy,TradingWay
import datetime
class Strategy(BaseStrategy):
    params=(
            ('period',20),
            ('devfac',2),
)
    def __init__(self):
        super().__init__()
        self.order=None
        self.bollinger=bt.indicators.BollingerBands(
                self.close_price(0),
                period=self.p.period,
                devfactor=self.p.devfac
            )
        self.bollinger_top=self.bollinger.top
        self.bollinger_mid=self.bollinger.mid
        self.bollinger_bot=self.bollinger.bot
    def next(self):
        if self.broker.getposition(self.data).size == 0:
            self.order=self.sell(
                exectype=bt.Order.Stop,
                size=self.broker.get_value()*self.p.position_to_balance/self.bollinger_top[0],
                price=self.bollinger_top[0],
                valid=self.data.datetime.date(0)+datetime.timedelta(days=1),
                )
        
            self.order=self.buy(
                exectype=bt.Order.Stop,
                size=self.broker.get_value()*self.p.position_to_balance/self.bollinger_bot[0],
                price=self.bollinger_bot[0],
                valid=self.data.datetime.date(0)+datetime.timedelta(days=1),
                )
        if self.broker.getposition(self.data).size > 0:
            if self.low_price[0]<self.bollinger_mid[0]:
                self.close()
        if self.broker.getposition(self.data).size < 0:
            if self.high_price[0]<self.bollinger_mid[0]:
                self.close()

    def gen_trading_signal(self)-> TradingWay:
            real_position=self.client.get_certain_position(self.p.pair)
            if real_position is None:
                return
            if real_position > 0:
                if self.close_price[0]<self.bollinger_mid[0]:
                    return TradingWay.CLOSE
            if real_position <0:
                if self.close_price[0]>self.bollinger_mid[0]:
                    return TradingWay.CLOSE
            if real_position==0:
                if self.close_price[0]>self.bollinger_top[0]:
                    return TradingWay.CLOSE_THEN_SHORT
                if self.close_price[0]<self.bollinger_bot[0]:
                    return TradingWay.CLOSE_THEN_LONG
