from bt_crypto.strategies.base import BaseStrategy, TradingWay
import backtrader as bt
import datetime

class Strategy(BaseStrategy):
    params = (
        ('volume_percent', 1),
        ("moving_period", 20),
        ("tb_period", 20),
        ("quit_period", 10),
    )

    def __init__(self):
        super().__init__()
        self.volume_avg = bt.indicators.Average(self.data.volume, period=self.p.moving_period)
        
        # Use data lines instead of methods
        self.DonchianH_entry = bt.indicators.Highest(self.data.high, period=self.params.tb_period)
        self.DonchianL_entry = bt.indicators.Lowest(self.data.low, period=self.params.tb_period)

        self.DonchianH_exit = bt.indicators.Highest(self.data.high, period=self.params.quit_period)
        self.DonchianL_exit = bt.indicators.Lowest(self.data.low, period=self.params.quit_period)

    def next(self):
        if_volume = self.data.volume[0] > self.volume_avg[-1] * (1 + self.p.volume_percent)
        
        if self.broker.getposition(self.data).size > 0:
            self.close()
        
        if self.data.close[0] > self.DonchianH_entry[-1] and if_volume:
            size = self.broker.get_value() * 0.3 / self.data.close[0]
            self.buy(size=size)
        
        elif self.data.close[0] < self.DonchianL_entry[-1] and if_volume:
            size = self.broker.get_value() * 0.3 / self.data.close[0]
            self.sell(size=size)
