from bt_crypto.strategies.base import BaseStrategy
from bt_crypto.indicators.NW import NW

class Strategy(BaseStrategy):
    params = (
        ('profit_pct', 0.005),  # 止盈比例 0.5%
        ('stop_pct', 0.003),    # 止损比例 0.3%
        ('risk_pct', 0.2),     # 每次交易风险比例 2%
        ('period', 20),
        ('h', 6.0),
        ('mult', 3.0),
    )
    
    def __init__(self):
        super().__init__()
        self.nw = NW(period=self.p.period,h=self.p.h,mult=self.p.mult)
        self.order = None
        self.entry_price = None
        
        # 记录上一个周期的状态
        self.above_upper = False  # 是否在上轨之上
        self.below_lower = False  # 是否在下轨之下
        
    def next(self):
        if self.order:
            return
            
        # 更新价格相对于通道的位置
        current_above_upper = self.close_price[0] > self.nw.upper[0]
        current_below_lower = self.close_price[0] < self.nw.lower[0]
        
        position = self.position.size
        
        # 计算仓位大小
        def calculate_size(price):
            risk_amount = self.broker.get_value() * self.p.risk_pct
            size = risk_amount / (price * self.p.stop_pct)
            size = round(size, 3)  # 四舍五入到0.001
            return max(0.001, min(size, 0.1))  # 限制最大仓位
        
        if position == 0:  # 没有持仓
            # 做多信号：之前在下轨之下，现在上穿下轨
            if self.below_lower and not current_below_lower:
                price = self.close_price[0]
                size = 20000 / price 
                self.order = self.buy(size=size)
                self.entry_price = price
                
            # 做空信号：之前在上轨之上，现在下穿上轨
            elif self.above_upper and not current_above_upper:
                price = self.close_price[0]
                size = 20000 / price 
                self.order = self.sell(size=size)
                self.entry_price = price
                
        else:  # 有持仓
            if position > 0:  # 多头持仓
                # 止盈条件
                if self.close_price[0] >= self.entry_price * (1 + self.p.profit_pct):
                    self.order = self.sell(size=position)
                # 止损条件
                elif self.close_price[0] <= self.entry_price * (1 - self.p.stop_pct):
                    self.order = self.sell(size=position)
                    
            else:  # 空头持仓
                # 止盈条件
                if self.close_price[0] <= self.entry_price * (1 - self.p.profit_pct):
                    self.order = self.buy(size=abs(position))
                # 止损条件
                elif self.close_price[0] >= self.entry_price * (1 + self.p.stop_pct):
                    self.order = self.buy(size=abs(position))
        
        # 更新状态
        self.above_upper = current_above_upper
        self.below_lower = current_below_lower