from datetime import datetime
import re
import os
import sys
import json
from typing import Dict, List
import pandas as pd
class BacktestConfig:
    """处理回测相关的配置"""
    def __init__(self):
        with open('db.json', 'r') as f:
            self.config = json.load(f)
    
    def get_pairs(self) -> List[str]:
        """获取所有配置的交易对"""
        return list(self.config['data']['pairs'].keys())
    def get_strategies(self)->List[str]:
        return list(self.config['strategy'].keys())
    
    def get_pair_config(self, pair: str) -> Dict:
        """获取指定交易对的配置"""
        return self.config['data']['pairs'][pair]
    
    def get_cerebro_config(self) -> Dict:
        """获取cerebro的基本配置"""
        return self.config['cerebro']
    
    def get_strategy_config(self, strategy: str) -> Dict:
        """获取指定策略的配置"""
        return self.config['strategy'][strategy]
    def get_basic_setting(self)->Dict:
        return self.config['basic_setting']
class DataCleaner:
    def pd_toflo(self,df:pd.DataFrame,column_indices:List[int]):
        for index in column_indices:
            name=df.columns[index]
            if df[name].dtype == object:
                df[name]=df[name].str.replace(',','').astype(float)
            else:
                df[name]= df[name].astype(float)
        print(df.head())
        return df
    def num_abbr_conv(self,df:pd.DataFrame,column_indices:List[int]):
        def _convert(s):
            if s is None:
                return
            print(s)
            s=str(s).replace(',','').strip()
            match = re.match(r'([\d\.]+)([KMB]?)', s)
            num = float(match.group(1))
            unit = match.group(2)
            if match:
                if unit =='K':
                    num *= 1e3
                if unit == 'M':
                    num *= 1e6
                if unit == 'B':
                    num *= 1e9
            return num
        for index in column_indices:
            name = df.columns[index]
            df[name]=df[name].apply(_convert)
        return df
    def tm_date_conv(self,ts:str):
       date_obj=datetime.fromtimestamp(ts/1000)
       result=date_obj.strftime("%Y-%m-%d %H:%M:%S")
       return result

def load_configs():
    """一次性加载所有配置"""
    backtest = BacktestConfig()
    return backtest
