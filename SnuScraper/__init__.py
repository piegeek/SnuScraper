import json
import sqlalchemy as db

config = dict()

with open('SnuScraper.cfg', 'r+', encoding='utf-8') as config_file:
    config_data = json.loads(config_file.read())
    
    config['DATABASE_URI'] = config_data['DATABASE_URI']
    config['SITE_URL'] = config_data['SITE_URL']
    
    with open(config_data['PARAMS_FILE'], 'r+', encoding='utf-8') as params:
        config['PARAMS'] = json.loads(params.read())

engine = db.create_engine(config['DATABASE_URI'])