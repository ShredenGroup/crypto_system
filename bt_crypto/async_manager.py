import asyncio
import pandas as pd
import aiohttp
import aiofiles
import json
from datetime import datetime

class AsyncManager(object):
    def __init__(self,config:Config,db:DataBase):
        self.config=config
        self.db=db
        self.api_manager=ApiManager(config,db)
        
    async def get_kline(self,symbol:str,interval:str,start_time:str=None,end_time:str=None)->pd.DataFrame:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={start_time}&endTime={end_time}') as response:
                return await response.json()
                
                
