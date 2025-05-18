import backtrader as bt
import numpy as np

class Ribeiro(bt.Indicator):
    """
    Ribeiro Indicator - Price Efficiency Indicator
    
    This indicator calculates the efficiency of price movements by comparing
    the total price change to the sum of absolute price changes.
    
    Formula:
    efficiency = (last_price - first_price) / sum(|price_changes|)
    
    The indicator ranges from -1 to 1:
    - Close to 1: Strong upward trend
    - Close to -1: Strong downward trend
    - Close to 0: Choppy/oscillating market
    """
    lines = ('efficiency',)
    params = (
        ('period', 14),  # Lookback period for calculation
    )
    
    def __init__(self):
        super(Ribeiro, self).__init__()
        
        # Calculate price differences
        self.price_diff = bt.indicators.Diff(self.data)
        
        # Calculate running sum of absolute differences
        self.abs_diff_sum = bt.indicators.SumN(self.price_diff, period=self.p.period)
        
        # Calculate total price change over the period
        self.total_change = self.data - self.data(-self.p.period)
        
        # Calculate efficiency
        self.lines.efficiency = self.total_change / self.abs_diff_sum
        