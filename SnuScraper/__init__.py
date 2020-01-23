import json
import logging
from os.path import abspath, join, dirname

from pymongo import MongoClient

config = dict()

with open('SnuScraper.cfg', 'r+', encoding='utf-8') as config_file:
    config_data = json.loads(config_file.read())
    
    config['CONNECTION_STRING'] = config_data['CONNECTION_STRING']
    config['SITE_URL'] = config_data['SITE_URL']
    config['EXCEL_URL'] = config_data['EXCEL_URL']
    config['LOG_FILE_PATH'] = abspath(join(dirname(__file__), '../log'))
    
    with open(config_data['PARAMS_FILE'], 'r+', encoding='utf-8') as params:
        config['PARAMS'] = json.loads(params.read())


client = MongoClient(config['CONNECTION_STRING'])

logger = logging.getLogger('SnuScraper')
hdlr = logging.FileHandler(join(config['LOG_FILE_PATH'], 'snuscraper.log'))
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)