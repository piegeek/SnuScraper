import requests
from SnuScraper import SITE_URL, PARAMS

class SnuScraper(object):

    def __init__(self):
        '''
        site_url: URL of server
        params: Parameters for a post request
        time_interval: Send a request at every 'time_interval' milliseconds 
        '''
        self._site_url = SITE_URL
        self._params = PARAMS
        self._time_interval = 3000

    def set_time_interval(self, time_interval):
        self._time_interval = time_interval
    
    def write_to_spread_sheet(self):
        '''
        Make a post request to the server with adequate parameters 
        then save the retrieved data to an excel file
        '''        
        res = requests.post(self._site_url, self._params)

        with open('./test.xls', 'wb') as output_file:
            output_file.write(res.content)

    def run(self):
        '''
        Send a request to the server and update the spreadsheet
        every 'time_interval' milliseconds 
        '''
        
