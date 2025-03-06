import os
import pandas as pd
from typing import List,Dict,Any
import pymysql as sql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from enum import Enum
from utils import DataCleaner
class datatype(Enum):
    pass
class sqldb():
    def __init__(self):
        self.utils=DataCleaner()
        self.conn=sql.connect(host='localhost',user='litterpigger',passwd='lhb1999114',port=3306)
        self.db_init()
    @contextmanager
    def db_cursor(self,db_name:str='crypto',table_name:str=None):
        cursor=self.conn.cursor(DictCursor)
        if db_name is not None:
            cursor.execute(
            f'use {db_name}'
            )
        yield cursor
        self.conn.commit()
        cursor.close()
    def db_dropper(self,db_name='crypto'):
        with self.db_cursor(db_name=None) as cursor:
            cursor.execute(f'drop database {db_name}')
            print(f'database {db_name} has been dropped')
    def db_init(self):
        with self.db_cursor() as cursor:
            cursor.execute("""
                   create database if not exists crypto
                   """)
    def show_all_db(self):
        with self.db_cursor('crypto') as cursor:
            cursor.execute("""
            show databases
            """
            )
            result=cursor.fetchall()
            print(result)
            return result
    def insert_pricesec(self,open,high,close,low,symbol,volume,sec):
        with self.db_cursor() as cursor:
            select_sql='select id from coin where name=%s'
            cursor.execute(select_sql,symbol)
            result=cursor.fetchone()['id']
            sql='insert into price_sec (open,high,close,low,coin_id,volume,ts_sec) values (%s,%s,%s,%s,%s,%s,%s)'
            data=(open,high,close,low,result,volume,sec)
            cursor.execute(sql,data)
            print('success')
    def insert_dprice(self,symbol,date,close,open,high,low,volume):
        with self.db_cursor() as cursor:
            select_sql='select id from coin where name=%s'
            cursor.execute(select_sql,symbol)
            result=cursor.fetchone()['id']
            sql='insert into price_daily (open,high,close,low,coin_id,volume,ts_day) values (%s,%s,%s,%s,%s,%s,%s)'
            data=(open,high,close,low,result,volume,date)
            cursor.execute(sql,data)
    def read_csv(self,path):
            data=pd.read_csv(path)
            data.drop(data.columns[-1],axis=1,inplace = true)
            data=self.utils.pd_toflo(data,[1,2,3,4])
            data=self.utils.num_abbr_conv(data,[5])
            values=list(data.values)
            for value in values:
                tup_value=tuple(value)
                self.insert_dprice('ethusdt',*tup_value)
    def read_multi_csv(self,path):
        with self.db_cursor() as cursor:
            BATCH_SIZE=50000
            result=os.walk(path)
            csv_files=[]
            for root,dic,files in result:
                for file in files:
                    if file.endswith('.csv'):
                        csv_file_path=f'{root}/{file}'
                        csv_files.append(csv_file_path)
            elements = csv_files[0].split('-')
            file_path=elements[0]
            interval=elements[1]
            symbol=file_path.split('/')[-1]
            self.insert_coin(symbol)
            coin_id=self.get_coin_id(symbol)
            for file in csv_files:
                elements=file.split('-')
                file_path=elements[0]
                symbol=file_path.split('/')[-1]
                interval=elements[1]
                data=pd.read_csv(file,header=None)
                data.drop(labels=data.columns[6:],axis=1)
                values=list(data.values)
                for value in values:
                    ts_str=value[0]
                    date_str=self.utils.tm_date_conv(float(ts_str))
                    open_price=float(value[1])
                    high_price=float(value[2])
                    low_price=float(value[3])
                    close_price=float(value[4])
                    volume=float(value[5])
                    sql='insert into price_sec (open,high,close,low,coin_id,volume,ts_sec) values (%s,%s,%s,%s,%s,%s,%s)'
                    data=(open_price,high_price,close_price,low_price,coin_id,volume,date_str)
                    cursor.execute(sql,data)
    def read_multi_csv(self, path):
    # Use a larger batch size for better performance
        BATCH_SIZE = 50000
        with self.db_cursor() as cursor:
            # Get all CSV files at once using list comprehension
            csv_files = [
                os.path.join(root, file)
                for root, _, files in os.walk(path)
                for file in files
                if file.endswith('.csv')
            ]
            batch_values=[] 
            for file in csv_files:
                # Extract symbol and interval from filename
                elements = file.split('-')
                symbol = elements[0].split('/')[-1]
                self.insert_coin(symbol)
                coin_id=self.get_coin_id(symbol)
                interval = elements[1]
                # Read CSV more efficiently
                df = pd.read_csv(
                    file,
                    header=None,
                    usecols=[0, 1, 2, 3, 4, 5],  # Only read needed columns
                    dtype={  # Specify dtypes for better performance
                        0: int,  # timestamp
                        1: float,  # open
                        2: float,  # high
                        3: float,  # low
                        4: float,  # close
                        5: float   # volume
                    }
                )

                # Process data in batches
                sql = 'INSERT INTO price_sec (open, high, close, low, coin_id, volume, ts_sec) VALUES (%s, %s, %s, %s, %s, %s, %s)'

                for _, row in df.iterrows():
                    date_str = self.utils.tm_date_conv(row[0])
                    batch_values.append((
                        row[1],  # open_price
                        row[2],  # high_price
                        row[4],  # close_price
                        row[3],  # low_price
                        coin_id,       # coin_id
                        row[5],  # volume
                        date_str
                    ))

                    # Execute batch insert when batch size is reached
                    if len(batch_values) >= BATCH_SIZE:
                        cursor.executemany(sql, batch_values)
                        batch_values = []
                # Insert any remaining records
            if batch_values:
                 cursor.executemany(sql, batch_values)
    def insert_coin(self,name):
        with self.db_cursor() as cursor:
            sql='insert into coin (name) values (%s)'
            data=(name)
            cursor.execute(sql,data)
    def get_coin_id(self,symbol):
        with self.db_cursor() as cursor:
            sql='SELECT id FROM coin WHERE name = %s'
            data=(symbol,)
            cursor.execute(sql,data)
            return cursor.fetchone().get('id')
    def create_factor_table(self):
        with self.db_cursor() as cursor:

db=sqldb() 
result=db.read_multi_csv("/home/litterpigger/data/data/spot/monthly/klines/TURBOUSDT/1m")
