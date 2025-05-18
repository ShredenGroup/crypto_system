import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from bt_crypto.indicators.Ribeiro import Ribeiro

class ICStrategy(bt.Strategy):
    params = (
        ('period', 14),
        ('forward_period', 5),  # 未来收益的周期
    )

    def __init__(self):
        self.ribeiro = Ribeiro(self.data, period=self.p.period)
        self.forward_returns = bt.indicators.ROC(self.data, period=self.p.forward_period)
        
        # 存储因子值和未来收益
        self.factor_values = []
        self.returns_values = []
        self.dates = []

    def next(self):
        # 记录因子值和未来收益
        self.factor_values.append(self.ribeiro.efficiency[0])
        self.returns_values.append(self.forward_returns[0])
        self.dates.append(self.data.datetime.date(0))

    def stop(self):
        # 计算IC
        df = pd.DataFrame({
            'date': self.dates,
            'factor': self.factor_values,
            'returns': self.returns_values
        })
        
        # 计算每日IC
        daily_ic = df.groupby('date').apply(
            lambda x: x['factor'].corr(x['returns'])
        )
        
        # 计算IC统计量
        ic_mean = daily_ic.mean()
        ic_std = daily_ic.std()
        ic_ir = ic_mean / ic_std  # Information Ratio
        ic_positive_ratio = (daily_ic > 0).mean()
        
        print("\n=== Ribeiro Factor IC Analysis ===")
        print(f"Period: {self.p.period}")
        print(f"Forward Period: {self.p.forward_period}")
        print(f"IC Mean: {ic_mean:.4f}")
        print(f"IC Std: {ic_std:.4f}")
        print(f"IC IR: {ic_ir:.4f}")
        print(f"IC > 0 Ratio: {ic_positive_ratio:.2%}")
        
        # 保存结果到CSV
        df.to_csv(f'ribeiro_ic_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')

def run_ic_test(data_path, period=14, forward_period=5):
    cerebro = bt.Cerebro()
    
    # 加载数据
    data = bt.feeds.GenericCSVData(
        dataname=data_path,
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        dtformat='%Y-%m-%d'
    )
    
    cerebro.adddata(data)
    cerebro.addstrategy(ICStrategy, period=period, forward_period=forward_period)
    
    # 运行回测
    cerebro.run()

if __name__ == '__main__':
    # 示例使用
    data_path = 'path_to_your_data.csv'  # 替换为实际数据路径
    run_ic_test(data_path, period=14, forward_period=5) 