from binance.um_futures import UMFutures
from datetime import datetime, timedelta, timezone
import time

# 替换为你的API Key和Secret
api_key = './Private_key'
api_secret = 'MTXEJs8Qr2vGGS80cFPcQv3wGMp1lS34icsvAv6ViPVrh9uB8A33n8v1Oc59McKL'


def main():

    timegap = 1

    # 创建客户端
    client = UMFutures(key=api_key, private_key=api_secret)
    
    # 定义开始和结束日期为 UTC 时间
    start_date = datetime(2025, 3, 1)
    end_date = datetime(2025, 3, 27)

    print(start_date)
    print(end_date)

    # 当前请求的开始时间
    current_start_time = start_date
    
    # 打开一个文件以写入 SQL 语句
    with open('klines_data_' + str(timegap) + 'm.sql', 'w') as f:
        # 写入 SQL 文件头
        f.write("USE binance;\n")
        f.write("CREATE TABLE IF NOT EXISTS klines_" + str(timegap) + "m (\n")
        f.write("    open_time_string datetime,\n")
        f.write("    open_time BIGINT,\n")
        f.write("    open_price DECIMAL(18, 8),\n")
        f.write("    high_price DECIMAL(18, 8),\n")
        f.write("    low_price DECIMAL(18, 8),\n")
        f.write("    close_price DECIMAL(18, 8),\n")
        f.write("    volume DECIMAL(18, 8),\n")
        f.write("    close_time BIGINT,\n")
        f.write("    quote_asset_volume DECIMAL(18, 8),\n")
        f.write("    number_of_trades INT,\n")
        f.write("    taker_buy_base_asset_volume DECIMAL(18, 8),\n")
        f.write("    taker_buy_quote_asset_volume DECIMAL(18, 8),\n")
        f.write("    token VARCHAR(10),\n")
        f.write("    PRIMARY KEY (open_time)\n")
        f.write(");\n\n")
        
        while current_start_time < end_date:
            # 计算当前请求的结束时间
            current_end_time = current_start_time + timedelta(minutes=1500 * timegap)
            if current_end_time > end_date:
                current_end_time = end_date
            
            # 获取数据
            result = client.klines(
                symbol='BTCUSDT',
                interval=str(timegap) + 'm',
                startTime=int(current_start_time.timestamp() * 1000),
                endTime=int(current_end_time.timestamp() * 1000),
                limit=1500
            )
            
            i = 0

            # 写入每一行数据为 SQL 插入语句
            for kline  in result:
                if i == 0:
                    print(kline[0])
                    # exit()

                i += 1

                datetime_obj = datetime.fromtimestamp(kline[0] / 1000)
                datestring = datetime.strftime(datetime_obj, '%Y-%m-%d %H:%M:%S')
                
                # open_time = datetime.fromtimestamp(kline[0] / 1000)
                f.write("INSERT INTO klines_" + str(timegap) + "m (open_time_string, open_time, open_price, high_price, low_price, close_price, volume, close_time, quote_asset_volume, number_of_trades, taker_buy_base_asset_volume, taker_buy_quote_asset_volume, token) VALUES (")
                f.write(f"'{datestring}', {kline[0]}, {kline[1]}, {kline[2]}, {kline[3]}, {kline[4]}, {kline[5]}, {kline[6]}, {kline[7]}, {kline[8]}, {kline[9]}, {kline[10]}, 'btc');\n")
            
            # 更新当前开始时间
            current_start_time = datetime_obj + timedelta(minutes=1 * timegap)
            
            time.sleep(0.2)
    
    print("SQL 文件已生成：klines_data_" + str(timegap) + "m.sql")

    

if __name__ == "__main__":
    main()