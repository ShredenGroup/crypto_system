import configparser
import os 
import sys
CFG_FL="user.cfg"
ACCOUNT_SECTION="sub_account"
CEREBRO_SECTION="cerebro"
DATA_SECTION="data"
TURTLE_SECTION="turtle_strategy"

class Config:
    def __init__(self):
        config=configparser.ConfigParser()
        CFG_PATH = os.path.join(os.path.dirname(__file__), CFG_FL)
        if not os.path.exists(CFG_FL):
            print('No user.cfg file found under current dictionary')
            sys.exit(1)
        else:
            config.read(CFG_FL)
        self.API_KEY=config.get(ACCOUNT_SECTION,"API_KEY")
        secret_path=config.get(ACCOUNT_SECTION,"SECRET_KEY")
        try:
            with open (secret_path,'r') as f:
                self.API_SECRET=f.read().strip()
        except FileNotFoundError:
            self.API_SECRET=''
        self.INIT_BAL=config.get(CEREBRO_SECTION,"init_cash")
        self.START_DATE=config.get(DATA_SECTION,"start_date")
        self.END_DATE=config.get(DATA_SECTION,"end_date")
        self.COMMISSION=config.get(CEREBRO_SECTION,"commission")
