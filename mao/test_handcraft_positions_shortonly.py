from datetime import datetime
from os import listdir
from os.path import dirname, exists, join
from tqdm import tqdm
import pandas as pd
import numpy as np

LONG_POSITION = 1
SHORT_POSITION = -1
EXIT_POSITION = 0

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

def evaluate_strategy(
        data: pd.DataFrame,
        positions: list,
        exchange_fee: float = 0.001):
    """
    Evaluates a trading strategy.
    """
    positions = np.array(positions)
    close_price = data["Close"].to_numpy()
    all_returns = ((close_price[1:] - close_price[:-1]) / close_price[:-1])
    all_returns = np.append([0.0], all_returns)
    positions_prev = np.append([EXIT_POSITION], positions[:-1])
    strategy_returns = np.zeros_like(positions, dtype=np.float32)
    strategy_returns[positions_prev == LONG_POSITION] = all_returns[positions_prev == LONG_POSITION]
    strategy_returns[positions_prev == SHORT_POSITION] = -all_returns[positions_prev == SHORT_POSITION]
    change_positions = np.append([EXIT_POSITION], positions[:-1]) - positions
    exchange_fees = [(1 - exchange_fee) ** abs(change_position) for change_position in change_positions]
    strategy_returns = (1.0 + strategy_returns) * exchange_fees
    portfolio_value = np.cumprod(strategy_returns)
    return portfolio_value

class TradeShortOnly():
    def __init__(self, data):
        self.data = data
        self.time_index = list(range(len(self.data)))
        self.positions = np.array([np.nan] * len(self.data))
        self.shares = 0
        self.cash = 10000
        self.commission_perc = 0.001

    def run(self):
        close_price = self.data["Close"].to_numpy()
        current_close = close_price[:-1]
        future_close = close_price[1:]
        change_close = future_close - current_close
        change_close = np.append(change_close, [0.0])
        self.positions[change_close > 0] = EXIT_POSITION
        self.positions[change_close < 0] = SHORT_POSITION

        mask = np.isnan(self.positions)
        idx = np.where(~mask, np.arange(mask.size), 0)
        np.maximum.accumulate(idx, out=idx)
        self.positions[mask] = self.positions[idx[mask]]

        self.positions[0] = EXIT_POSITION
        self.positions[-1] = EXIT_POSITION

        
if __name__ == "__main__":
    data_folder = "/home/litterpigger/quant/crypto_system/mao/1d/csv"
    start_date = "2024-01-01"
    end_date = "2025-01-01"
    data = BitcoinDataReader(data_folder, start_date, end_date).get_data()
    trade = TradeShortOnly(data)
    trade.run()
    print(trade.positions)
    portfolio_value = evaluate_strategy(data, trade.positions, 0.001379)
    print(portfolio_value[-1] * trade.cash)
    # print(trade.positions, len(trade.positions))
