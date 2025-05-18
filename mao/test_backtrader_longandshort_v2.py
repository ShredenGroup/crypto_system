import backtrader as bt
from datetime import datetime
from os import listdir
from os.path import dirname, exists, join
from tqdm import tqdm
import pandas as pd


class BitcoinDataReader(object):
    def __init__(self, data_folder, start_date, end_date):
        self.data_folder = data_folder
        self.start_date = start_date
        self.end_date = end_date

    def read_all_csv(self, data_folder):
        pickle_file = join(dirname(data_folder), "data.pkl")
        if not exists(pickle_file):
            csv_files = [join(data_folder, f) for f in listdir(data_folder) if f.endswith(".csv")]
            df_list = []

            for file in tqdm(csv_files):
                df = pd.read_csv(file, header=None)
                first_timestamp = df.iloc[0,0]

                if first_timestamp > 10**13:
                    time_divisor = 1e6
                else:
                    time_divisor = 1e3

                df.columns = ["Open_Time", "Open", "High", "Low", "Close", "Volume", "Close_Time",
                        "Quote_Asset_Volume", "Number_of_Trades", "Taker_Buy_Base_Asset_Volume",
                        "Taker_Buy_Quote_Asset_Volume", "Ignore"]
                df["Open_Time"] = df["Open_Time"] / time_divisor
                df["Close_Time"] = df["Close_Time"] / time_divisor
                df_list.append(df)

            full_df = pd.concat(df_list, ignore_index=True)
            if full_df.index.duplicated().any():
                full_df = full_df[~full_df.index.duplicated()]
            full_df = full_df[["Open", "High", "Low", "Close", "Volume", "Open_Time", "Close_Time"]]
            full_df.to_pickle(pickle_file)
        else:
            full_df = pd.read_pickle(pickle_file)
        return full_df
    
    def get_data(self):
        split_data = {}
        all_data = self.read_all_csv(self.data_folder)
        start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(self.end_date, "%Y-%m-%d")
        data = all_data[(pd.to_datetime(all_data["Open_Time"], unit="s") >= start_date) & (pd.to_datetime(all_data["Open_Time"], unit="s") <= end_date)]
        data = data[["Open", "High", "Low", "Close", "Volume", "Close_Time", "Open_Time"]]
        return data

class MyPandasData(bt.feeds.PandasData):
    lines = ("close_time", )
    params = (
        ("close_time", -1),
    )

class TestBTShorterStrategy(bt.Strategy):
    params = (
        ('printlog', False),  # 是否打印日志
        ('commission', 0.001),
    )
    def __init__(self):
        self.count = 0
        self.order = None
        self.next_action = None
        self.current_price = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交/接受 - 无需操作
            return

        # 检查订单是否已完成
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'买入执行: 价格: {order.executed.price:.2f}, '
                    f'数量: {order.executed.size:.2f}, '
                    f'成本: {order.executed.value:.2f}, '
                    f'手续费: {order.executed.comm:.2f}'
                )
            else:
                self.log(
                    f'卖出执行: 价格: {order.executed.price:.2f}, '
                    f'数量: {order.executed.size:.2f}, '
                    f'成本: {order.executed.value:.2f}, '
                    f'手续费: {order.executed.comm:.2f}'
                )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')

        # 重置订单变量
        self.order = None

    def next(self):
        # print(len(self.data.close))
        if len(self.data.close) < 2:
            return
        if len(self.data.close) == 367:
            if self.position.size < 0:
                self.close()
            return

        current_price = self.data.close[0]
        future_price = self.data.close[1]
        self.current_price = current_price

        if future_price > current_price:
            if self.position.size < 0:
                self.log(f"SHORT TO LONG CREATE.")
                size_1 = abs(self.position.size)
                available_cash = self.broker.getvalue()
                close_short_cash = size_1 * current_price
                commission = close_short_cash * self.params.commission
                size_2 = (available_cash - close_short_cash - commission) / current_price
                # size_2 = 0
                all_size = size_1 + size_2
                self.order = self.buy(size=all_size)

            elif self.position.size >= 0:
                self.log(f"LONG CREATE.")
                cash = self.broker.getvalue()
                available_cash = cash * (1 - self.params.commission)
                size = available_cash / current_price
                self.order = self.buy(size=size)
        else:
            if self.position.size > 0:
                self.log(f"LONG TO SHORT CREATE.")
                size_1 = self.position.size
                available_cash = self.broker.getvalue()
                close_long_cash = size_1 * current_price
                commission = close_long_cash * self.params.commission
                size_2 = (available_cash + close_long_cash - commission) / current_price
                # size_2 = 0
                all_size = size_1 + size_2
                
                self.order = self.sell(size=all_size)
            elif self.position.size >= 0:
                self.log(f"SHORT CREATE")
                cash = self.broker.getvalue()
                available_cash = cash * (1 - self.params.commission)
                size = available_cash / current_price
                self.order = self.sell(size=size)

    def log(self, txt, dt=None, doprint=False):
        '''日志函数'''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')


if __name__ == "__main__":
    data_folder="/home/litterpigger/quant/crypto_system/mao/1d/csv"
    start_date = "2024-01-01"
    end_date = "2025-01-01"
    data = BitcoinDataReader(data_folder=data_folder, start_date=start_date, end_date=end_date).get_data()
    data["Close_Time_Ref"] = pd.to_datetime(data["Close_Time"], unit="s")
    data = data.set_index("Close_Time_Ref")
    bt_data = MyPandasData(
        dataname=data,
        datetime=None,
        open="Open",
        high="High",
        low="Low",
        close="Close",
        volume="Volume",
        close_time="Close_Time",
        openinterest=-1
    )
    data_len = len(data)
    print(data_len)
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(30000.0)
    cerebro.adddata(bt_data)
    commission = 0.001
    cerebro.addstrategy(TestBTShorterStrategy, printlog=True, commission=commission)
    cerebro.broker.setcommission(commission=commission, stocklike=False)
    cerebro.run()
    print('最终资金: %.2f' % cerebro.broker.getvalue())
    cerebro.plot()