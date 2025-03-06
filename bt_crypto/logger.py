import logging
import os 
class Logger:
    def __init__(self,logging_name:str="live_trade"):
        self.Logger=logging.getLogger(f'{logging_name}_logger')
        self.Logger.setLevel(logging.DEBUG)
        if not self.Logger.handlers:
            formatter=logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            fh=logging.FileHandler(f'logs/{logging_name}.log')
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            self.Logger.addHandler(fh)

    def log(self,message,level="info"):
        if level=="info":
            self.Logger.info(message)
        elif level=="error":
            self.Logger.error(message)
        elif level=="warning":
            self.Logger.warning(message)
    def info(self,message):
        self.log(message,"info")
    def error(self,message):
        self.log(message,"error")
    def warning(self,message):
        self.log(message,"warning")

