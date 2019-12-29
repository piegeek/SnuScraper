import json
from pymongo import MongoClient

config = dict()

with open('SnuScraper.cfg', 'r+', encoding='utf-8') as config_file:
    config_data = json.loads(config_file.read())
    
    config['CONNECTION_STRING'] = config_data['CONNECTION_STRING']
    config['SITE_URL'] = config_data['SITE_URL']
    
    with open(config_data['PARAMS_FILE'], 'r+', encoding='utf-8') as params:
        config['PARAMS'] = json.loads(params.read())


client = MongoClient(config['CONNECTION_STRING'])
db = client.SnuScraperLocalTest