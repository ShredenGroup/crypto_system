import backtrader as bt
from bt_crypto.strategies.base import BaseStrategy,TradingWay
import datetime
import os
import csv

class Strategy(BaseStrategy):
    params = (
        ('period', 20),        # 布林带周期
        ('devfac', 2),        # 布林带标准差倍数
        ('size', 20000),      # 开仓金额
        ('stop_loss', 0.01),  # 止损比例 1%
        ('rsi_low', 30),      # RSI超卖阈值
        ('rsi_high', 70),     # RSI超买阈值
    )
    
    def __init__(self):
        # 先调用父类的初始化
        super().__init__()
        
        self.order = None
        self.stop_order = None
        self.profit_order = None
        
        # 指标
        self.rsi = bt.indicators.RSI(self.close_price(0), period=14)
        self.bollinger = bt.indicators.BollingerBands(
            self.close_price(0),
            period=self.p.period,
            devfactor=self.p.devfac
        )
        self.bollinger_top = self.bollinger.top
        self.bollinger_mid = self.bollinger.mid
        self.bollinger_bot = self.bollinger.bot
        
        # 记录开仓价格
        self.entry_price = None
        
        # 添加分析器
        self.analyzers.trades = bt.analyzers.TradeAnalyzer()
        
        # 创建CSV文件并写入表头
        self.csv_file = os.path.join('data', 'trade_records.csv')
        os.makedirs('data', exist_ok=True)
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'action', 'price', 'quantity', 'value', 'fees', 'rsi', 'bollinger_mid'])
        
    def log_to_csv(self, action, price, quantity, value, fees, rsi=None, bollinger_mid=None):
        """将交易记录写入CSV文件"""
        current_time = bt.num2date(self.datetime[0]).strftime('%Y-%m-%d %H:%M:%S')
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([current_time, action, f'{price:.4f}', f'{quantity:.2f}', 
                           f'{value:.2f}', f'{fees:.2f}', 
                           f'{rsi:.2f}' if rsi is not None else '',
                           f'{bollinger_mid:.4f}' if bollinger_mid is not None else ''])
        
    def next(self):
        # 如果有未完成的订单，等待
        if self.order:
            return
            
        # 当前持仓
        position_size = self.position.size
        current_time = bt.num2date(self.datetime[0]).strftime('%Y-%m-%d %H:%M:%S')
        
        if position_size == 0:  # 没有持仓
            # 买入信号：价格下破布林带下轨且RSI < 30
            if self.close_price[0] < self.bollinger_bot[0] and self.rsi[0] < self.p.rsi_low:
                # 计算购买数量
                size = self.p.size / self.close_price[0]
                self.order = self.buy(size=size)
                self.entry_price = self.close_price[0]
                print(f'[{current_time}] 买入信号 - 价格: {self.close_price[0]:.4f}, RSI: {self.rsi[0]:.2f}')
                # 记录买入信号
                self.log_to_csv('buy_signal', self.close_price[0], size, self.p.size, 2.00, self.rsi[0])
                
        else:  # 有持仓
            # 卖出信号：价格上破布林带上轨且RSI > 70
            if self.close_price[0] > self.bollinger_top[0] and self.rsi[0] > self.p.rsi_high:
                self.order = self.close()
                print(f'[{current_time}] 卖出信号 - 价格: {self.close_price[0]:.4f}, RSI: {self.rsi[0]:.2f}')
                # 记录卖出信号
                self.log_to_csv('sell_signal', self.close_price[0], -position_size, 
                              position_size * self.close_price[0], 2.00, 
                              bollinger_mid=self.bollinger_mid[0])
                return
                
            # 止损：价格低于开仓价格的1%
            stop_price = self.entry_price * (1 - self.p.stop_loss)
            if self.close_price[0] < stop_price:
                self.order = self.close()
                print(f'[{current_time}] 止损触发 - 价格: {self.close_price[0]:.4f}, 止损价: {stop_price:.4f}')
                # 记录止损信号
                self.log_to_csv('stop_loss', self.close_price[0], -position_size,
                              position_size * self.close_price[0], 1.98)
                return
            
            # 移动止盈：当价格突破布林带中轨时卖出
            if self.close_price[0] > self.bollinger_mid[0]:
                self.order = self.close()
                print(f'[{current_time}] 移动止盈触发 - 价格: {self.close_price[0]:.4f}, 中轨: {self.bollinger_mid[0]:.4f}')
                # 记录移动止盈信号
                self.log_to_csv('profit_take', self.close_price[0], -position_size,
                              position_size * self.close_price[0], 2.00,
                              bollinger_mid=self.bollinger_mid[0])
                return

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        current_time = bt.num2date(self.datetime[0]).strftime('%Y-%m-%d %H:%M:%S')
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'[{current_time}] 买入执行 - 价格: {order.executed.price:.4f}, 数量: {order.executed.size:.2f}, 价值: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}')
                # 记录买入执行
                self.log_to_csv('buy_executed', order.executed.price, order.executed.size,
                              order.executed.value, order.executed.comm)
            else:
                print(f'[{current_time}] 卖出执行 - 价格: {order.executed.price:.4f}, 数量: {order.executed.size:.2f}, 价值: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}')
                # 记录卖出执行
                self.log_to_csv('sell_executed', order.executed.price, order.executed.size,
                              order.executed.value, order.executed.comm)
                self.entry_price = None  # 清除入场价格

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print(f'[{current_time}] 订单取消/保证金不足/拒绝')
            # 记录订单取消
            self.log_to_csv('order_canceled', self.close_price[0], 0, 0, 0)

        self.order = None  # 重置订单

    def stop(self):
        # 调用父类的stop方法
        super().stop()
        
        # 获取回测结果
        portfolio_value = self.broker.getvalue()
        starting_value = self.broker.startingcash
        
        print('\n策略回测结果:')
        print('=' * 50)
        
        # 计算总收益
        total_return = (portfolio_value / starting_value - 1.0)
        print(f'初始资金: {starting_value:.2f}')
        print(f'期末资金: {portfolio_value:.2f}')
        print(f'总收益率: {total_return:.2%}')
            
        # 获取交易统计
        trade_analysis = self.analyzers.trades.get_analysis()
        print('\n交易统计:')
        
        # 总交易次数
        total_trades = trade_analysis.get('total', {}).get('total', 0)
        print(f'总交易次数: {total_trades}')
        
        if total_trades > 0:
            # 获取已完成交易
            closed_trades = trade_analysis.get('total', {}).get('closed', 0)
            print(f'已完成交易: {closed_trades}')
            
            # 获取盈利交易
            won_trades = trade_analysis.get('won', {}).get('total', 0)
            if won_trades > 0:
                avg_won = trade_analysis['won']['pnl']['average']
                max_won = trade_analysis['won']['pnl']['max']
                print(f'盈利交易: {won_trades}')
                print(f'平均盈利: {avg_won:.2f}')
                print(f'最大盈利: {max_won:.2f}')
            
            # 获取亏损交易
            lost_trades = trade_analysis.get('lost', {}).get('total', 0)
            if lost_trades > 0:
                avg_lost = trade_analysis['lost']['pnl']['average']
                max_lost = trade_analysis['lost']['pnl']['max']
                print(f'亏损交易: {lost_trades}')
                print(f'平均亏损: {avg_lost:.2f}')
                print(f'最大亏损: {max_lost:.2f}')
            
            # 计算胜率
            if closed_trades > 0:
                win_rate = won_trades / closed_trades
                print(f'胜率: {win_rate:.2%}')
            
            # 获取总盈亏
            if 'pnl' in trade_analysis:
                total_pnl = trade_analysis['pnl'].get('net', {}).get('total', 0)
                print(f'总盈亏: {total_pnl:.2f}')
        else:
            print('无交易记录')
        
        print('=' * 50)