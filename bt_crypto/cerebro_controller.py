from typing import List,Tuple
from .strategies import get_strategy
import backtrader as bt
from .config import Config
from .api_manager import ApiManager
from datetime import datetime
from .utils import load_configs
from .db import DataBase
from .logger import Logger
class CerebroController():
    def __init__(self,db):
        self.config=Config()
        self.cerebro=bt.Cerebro()
        self.client=ApiManager(self.config,db)
        self.bt_config=load_configs()
    def cerebro_init(self)->bt.Cerebro:
        cerebro=bt.Cerebro()
        cerebro.broker.setcash(float(self.config.INIT_BAL))
        cerebro.broker.setcommission(commission=float(self.config.COMMISSION))
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        return cerebro
    def single_strategy_runner(self,curr_strategy=None):
        cerebro=self.cerebro_init()
        data=self._get_trading_data()
        cerebro.adddata(data)
        str_strategy=self.bt_config.get_cerebro_config()['curr_strategy']
        strategy=get_strategy(curr_strategy or str_strategy)
        base_strategy_params=self.bt_config.get_basic_setting()
        cerebro.addstrategy(strategy,**base_strategy_params)
        cerebro.run()
    def multiple_strategy_runner(self,multi_strategies:List[str]=None):
        strategy_list:[str]=multi_strategies or self.bt_config.get_cerebro_config()['mult_strategies'].strip().split(',')
        base_strategy_params:Dict=self.bt_config.get_basic_setting()
        for strategy in strategy_list:
            strategy_module=get_strategy(strategy)
            cerebro=self.cerebro_init()
            data=self._get_trading_data()
            cerebro.adddata(data)
            cerebro.addstrategy(strategy_module,**base_strategy_params)
            cerebro.run()
    def _get_trading_data(self,pair:str=None)->bt.feeds.PandasData:
        trading_pair=self.bt_config.get_basic_setting()['pair']
        curr_pair=pair or trading_pair
        ava_list=self.bt_config.get_pairs()
        if curr_pair in ava_list:
            pair_config=self.bt_config.get_pair_config(curr_pair)
            df=self.client.get_kline(
            symbol=curr_pair,
            **pair_config
        )
        data=bt.feeds.PandasData(dataname=df,datetime=None,open=-1,low=-1,high=-1) 
        return data 
    def all_strategy_runner(self):
        pairs=self.bt_config.get_pairs()
        strategies=self.bt_config.get_strategies()
        for pair in pairs:
            pair_info=self.bt_config.get_pair_config(pair)
            start_time=pair_info['start_time']
            end_time=pair_info['end_time']
            interval=pair_info['interval']
            df=self.client.get_kline(
                symbol=pair,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
            )
            start_time=datetime.strptime(pair_info['start_time'],'%Y%m%d')
            end_time=datetime.strptime(pair_info['end_time'],'%Y%m%d')
            data=bt.feeds.PandasData(dataname=df,datetime=None,open=-1,close=-1,low=-1,high=-1)
            for strategy in strategies:
                
                strategy_info=self.bt_config.get_strategy_config(strategy)
                origin_param=[param_config['start'] for param_config in strategy_info['parameters'].values()] 
                cerebro=self.cerebro_init()
                cerebro.adddata(data)
                strategy_module=get_strategy(strategy)
                if not strategy_info['opt_param']:
                    cerebro.addstrategy(strategy_module)
                    cerebro.run()
                else:
                    param=self._create_strategy_params(strategy_info)
                    base_strategy_params=self.bt_config.get_basic_setting()
                    opt_strategy=cerebro.optstrategy(strategy_module,**param,**base_strategy_params) 
                    results=cerebro.run(maxcpu=1)  
    def single_strategy_opt(self,curr_strategy=None):
        cerebro=self.cerebro_init()
        data=self._get_trading_data()
        cerebro.adddata(data)
        str_strategy=self.bt_config.get_cerebro_config()['curr_strategy']
        strategy=get_strategy(curr_strategy or str_strategy)
        strategy_info=self.bt_config.get_strategy_config(str_strategy)
        base_strategy_params=self.bt_config.get_basic_setting()
        param=self._create_strategy_params(strategy_info)
        cerebro.optstrategy(strategy,**param,**base_strategy_params)
        cerebro.run(maxcpu=1)
    def _create_strategy_params(self, strategy_info):
        params = {}
        for param_name, param_config in strategy_info['parameters'].items():
            if isinstance(param_config['start'], float):
                # 对于浮点数，创建一个浮点数序列
                values = []
                current = param_config['start']
                while current <= param_config['end']:
                    values.append(current)
                    current += param_config['step']
                params[param_name] = tuple(values)
            else:
                # 对于整数，使用 range
                params[param_name] = range(
                    param_config['start'],
                    param_config['end'] + param_config['step'],
                    param_config['step']
                )
        return params
