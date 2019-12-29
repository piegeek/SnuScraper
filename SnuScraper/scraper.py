import requests
import pandas as pd
from os.path import join
from SnuScraper import config

class SnuScraper(object):

    def __init__(self):
        '''
        site_url: URL of server
        params: Parameters for a post request
        time_interval: Send a request at every 'time_interval' milliseconds 
        '''
        self._site_url = config['SITE_URL']
        self._params = config['PARAMS']
        self._time_interval = 3000

    def set_time_interval(self, time_interval):
        self._time_interval = time_interval
    
    def get_spread_sheet(self):
        '''
        Make a post request to the server with adequate parameters 
        then save retrieved data to an excel file
        '''        
        res = requests.post(self._site_url, self._params)

        return res.content

    def save_spread_sheet(self, filename):
        '''
        Save response content(excel file) as given filename
        '''

        with open(join('xls', filename), 'wb') as output_file:
            output_file.write(self.get_spread_sheet())

    def load_spread_sheet(self):
        '''
        Load an excel spreadsheet into a pandas dataframe object
        '''
        df = pd.read_excel(self._xls_file)
        return df

    def save_to_db(self):
        pass

    def run(self):
        '''
        Send a request to the server and update spreadsheet
        every 'time_interval' milliseconds 
        '''
        pass


def init_scraper(scraper_app, year, season):
    seasons = ['SPRING', 'SUMMER', 'FALL', 'WINTER']
    if int(year) >= 2019 and season in seasons:
        scraper_app.save_spread_sheet(f'{year}-{season}.xls')
    else:
        raise ValueError(
            '''
            ERROR! Parameters for 'init_scraper' must be over 2018 and one of choices: 'SPRING', 'SUMMER', 'FALL', 'WINTER'
            '''
        )
