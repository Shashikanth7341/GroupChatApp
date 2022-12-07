import os

class Config(object):
    MONGO_URI = os.environ.get('MONGO_URI',"mongodb://localhost:27017/")