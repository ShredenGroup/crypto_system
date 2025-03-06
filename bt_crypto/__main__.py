import time
from .cerebro_controller import CerebroController
from .stream_manager import StreamManager
from .api_manager import ApiManager,Side
from .config import Config
from .utils import load_configs
from .logger import Logger
from .db import DataBase
def main():
    bt_config=load_configs()
    live_trade=bt_config.get_basic_setting()['livetrade']
    trading_logger=Logger('database')
    logger=Logger('live_trade')
    db=DataBase(logger=trading_logger)
    db.create_database()
    cerebro_core=CerebroController(db)
    cerebro_core.cerebro_init()
    if live_trade:
        #cerebro_core.all_strategy_runner()
        while True:
            try:
                start_time=time.time()
                cerebro_core.single_strategy_runner()
                end_time=time.time()
                execution_time = end_time - start_time
                print(f"Execution time: {execution_time:.2f} seconds")
            except Exception as e:
                logger.error(f"An eror occurred:{e}")
                time.sleep(5) 
    else:
            cerebro_core.single_strategy_runner()
            
    #cerebro_core.multiple_strategy_runner()
    #client=ApiManager(config)
    #client.place_order('DOGEUSDT',Side.BUY,order_type='MARKET',quantity=12)
main()
#config=Config()
#api_manager=ApiManager(config)
#api_manager.get_current_order()
#api_manager.place_order('DOGEUSDT',Side.BUY,'LIMIT',18,0.3,timeInForce='GTC')
#api_manager.cancel_order('DOGEUSDT')
#sm.get_price()  

