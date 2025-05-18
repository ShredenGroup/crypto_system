from bt_crypto.strategies.base import BaseStrategy
import backtrader as bt
import pandas as pd
import os
from datetime import datetime

class Strategy(BaseStrategy):
    params = (
        ('rsi_period', 14),
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
        ('bollinger_period', 20),
        ('bollinger_devfactor', 2),
        ('atr_period', 14),
        ('cci_period', 20),
        ('stoch_period', 14),
        ('stoch_period_d', 3),
        ('stoch_period_k', 3),
        ('willy_period', 14),
        ('mom_period', 10),
    )
    
    def __init__(self):
        super().__init__()
        
        # Price and Volume
        self.close_price = self.data.close
        self.high_price = self.data.high
        self.low_price = self.data.low
        self.volume = self.data.volume
        self.open_price = self.data.open
        
        # Moving Averages
        self.sma5 = bt.indicators.SMA(period=5)
        self.sma10 = bt.indicators.SMA(period=10)
        self.sma20 = bt.indicators.SMA(period=20)
        self.sma50 = bt.indicators.SMA(period=50)
        self.sma200 = bt.indicators.SMA(period=200)
        self.ema5 = bt.indicators.EMA(period=5)
        self.ema10 = bt.indicators.EMA(period=10)
        self.ema20 = bt.indicators.EMA(period=20)
        self.ema50 = bt.indicators.EMA(period=50)
        self.ema200 = bt.indicators.EMA(period=200)
        
        # Oscillators
        self.rsi = bt.indicators.RSI(period=self.p.rsi_period)
        self.macd = bt.indicators.MACD(
            period_me1=self.p.macd_fast,
            period_me2=self.p.macd_slow,
            period_signal=self.p.macd_signal
        )
        self.stoch = bt.indicators.Stochastic(
            period=self.p.stoch_period,
            period_dfast=self.p.stoch_period_d,
            period_dslow=self.p.stoch_period_k
        )
        
        # Volatility
        self.bollinger = bt.indicators.BollingerBands(
            period=self.p.bollinger_period,
            devfactor=self.p.bollinger_devfactor
        )
        self.atr = bt.indicators.ATR(period=self.p.atr_period)
        
        # Momentum
        self.cci = bt.indicators.CCI(period=self.p.cci_period)
        self.williams = bt.indicators.WilliamsR(period=self.p.willy_period)
        self.momentum = bt.indicators.Momentum(period=self.p.mom_period)
        
        # Store indicators data
        self.indicators_data = []
        
    def next(self):
        # Create dictionary with all indicator values
        indicators = {
            'datetime': self.data.datetime.date(0).isoformat(),
            'timestamp': self.data.datetime.datetime(0).timestamp(),
            'open': self.open_price[0],
            'high': self.high_price[0],
            'low': self.low_price[0],
            'close': self.close_price[0],
            'volume': self.volume[0],
            
            # Moving Averages
            'sma5': self.sma5[0],
            'sma10': self.sma10[0],
            'sma20': self.sma20[0],
            'sma50': self.sma50[0],
            'sma200': self.sma200[0],
            'ema5': self.ema5[0],
            'ema10': self.ema10[0],
            'ema20': self.ema20[0],
            'ema50': self.ema50[0],
            'ema200': self.ema200[0],
            
            # Oscillators
            'rsi': self.rsi[0],
            'macd': self.macd.macd[0],
            'macd_signal': self.macd.signal[0],
            'macd_hist': self.macd.macd[0] - self.macd.signal[0],
            'stoch_k': self.stoch.percK[0],
            'stoch_d': self.stoch.percD[0],
            
            # Volatility
            'bb_upper': self.bollinger.top[0],
            'bb_middle': self.bollinger.mid[0],
            'bb_lower': self.bollinger.bot[0],
            'bb_width': (self.bollinger.top[0] - self.bollinger.bot[0]) / self.bollinger.mid[0],
            'atr': self.atr[0],
            
            # Momentum
            'cci': self.cci[0],
            'williams_r': self.williams[0],
            'momentum': self.momentum[0],
        }
        
        self.indicators_data.append(indicators)
    
    def stop(self):
        # Convert to DataFrame and save to CSV
        df = pd.DataFrame(self.indicators_data)
        
        # 获取项目根目录
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(root_dir, "data", "indicators")
        
        # 确保目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        # 获取开始和结束时间
        start_time = df['datetime'].iloc[0]
        end_time = df['datetime'].iloc[-1]
        
        # 构建文件名：币种_开始日期_结束日期.csv
        filename = f"{self.p.pair}_{start_time}_{end_time}_indicators.csv"
        filepath = os.path.join(data_dir, filename)
        
        # 保存基础数据
        base_columns = ['datetime', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
        df[base_columns].to_csv(filepath.replace('_indicators.csv', '_base.csv'), index=False)
        
        # 保存指标数据
        df.to_csv(filepath, index=False)
        
        print(f"Base data saved to {filepath.replace('_indicators.csv', '_base.csv')}")
        print(f"Indicators data saved to {filepath}")
        
        # Call parent's stop method
        super().stop()