from bt_crypto.strategies.base import BaseStrategy,TradingWay
import backtrader as bt
import datetime
class Strategy(BaseStrategy):
    params=(
        ('open_period',20),
        ('close_period',10),
            )
    def __init__(self):
        super().__init__()
        self.DonchianH_entry=bt.indicators.Highest(self.high_price(0),period=self.params.open_period)
        self.DonchianL_exit=bt.indicators.Lowest(self.low_price(0),period=self.params.close_period)
        self.DonchianH_exit=bt.indicators.Highest(self.high_price(0),period=self.params.close_period)
        self.DonchianL_entry=bt.indicators.Lowest(self.low_price(0),period=self.params.open_period)
        self.order=None
    def next(self):
        if self.broker.getposition(self.data).size == 0:
            self.order=self.buy(
                exectype=bt.Order.Stop,
                size=self.broker.get_value()*self.p.position_to_balance/self.DonchianL_entry[0],
                price=self.DonchianH_entry[0],
                valid=self.data.datetime.date(0)+datetime.timedelta(days=1)
                )

            self.order=self.sell(exectype=bt.Order.Stop,size=self.broker.get_value()*self.p.position_to_balance/self.DonchianL_entry[0],price=self.DonchianL_entry[0],valid=self.data.datetime.date(0)+datetime.timedelta(days=1))
            
        if self.broker.getposition(self.data).size>0:
            if self.low_price[0]<self.DonchianL_exit[-1]:
                self.close()
        if self.broker.getposition(self.data).size<0:
            if self.high_price[0]>self.DonchianH_exit[-1]:
                self.close()
    def gen_trading_signal(self)-> TradingWay:
            real_position=self.client.get_certain_position(self.p.pair)
            if real_position is None:
                return
            if real_position > 0:
                if self.close_price[0]<self.DonchianL_exit[-1]:
                    return TradingWay.CLOSE
            if real_position <0:
                if self.close_price[0]>self.DonchianH_exit[-1]:
                    return TradingWay.CLOSE
            if real_position==0:
                if self.close_price[0]>self.DonchianH_entry[-1]:
                    return TradingWay.CLOSE_THEN_LONG
                if self.close_price[0]<self.DonchianL_entry[-1]:
                    return TradingWay.CLOSE_THEN_SHORT
