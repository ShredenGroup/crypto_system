import redis 
class Rd():
    def __init__(self):
        self.r=redis.Redis(host='localhost',port)