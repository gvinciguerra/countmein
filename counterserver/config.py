import os
from configparser import ConfigParser

config = ConfigParser({
    "MongoDBUri": "localhost"
})

path = os.path.join(os.path.dirname(__file__), "config.cfg")
config.read(path)
