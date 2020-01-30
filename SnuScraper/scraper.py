import requests
import json
import time
import pandas as pd
import firebase_admin
from firebase_admin import messaging
from os.path import join
from copy import copy, deepcopy
from bson.objectid import ObjectId
from bs4 import BeautifulSoup
from SnuScraper import config, logger

class SnuScraper(object):

    def __init__(self, year, season, id, max_page_num, db, debug=False):
        '''
        site_url: URL of server
        params: Parameters for a post request
        time_interval: Send a request at every 'time_interval' milliseconds 
        '''
        self._site_url = config['SITE_URL']
        self._excel_url = config['EXCEL_URL']
        self._params = copy(config['PARAMS'])
        self._time_interval = 3
        self.year = year
        self.id = id
        self.season = season
        self.max_page_num = max_page_num
        self.db = db
        self.admin = firebase_admin.initialize_app()
        self.debug = debug
        self.logger = logger

        self.set_params()

    def log_message(self, msg, log_level):
        if self.debug == True:
            print(msg)
        elif self.debug != True and log_level == 'info':
            self.logger.info(msg)
        elif self.debug != True and log_level == 'error':
            self.logger.info(msg)
        elif self.debug != True and log_level == 'warning':
            self.logger.warning(msg)

    def set_params(self):
        self._params['srchOpenSchyy'] = self.year
        self._params['currSchyy'] = self.year
        self._params['srchOpenShtm'] = self.id
        self._params['currShtmNm'] = self.season

    def set_time_interval(self, time_interval):
        '''
        Set the time interval(in minutes) for the scraper to send requests to the server
        and update the db after every specified time interval passes. 
        '''
        
        if 0 <= time_interval <=20:
            self._time_interval = time_interval
        else:
            raise ValueError('Parameter \'time_interval\' of function \'set_time_interval\' must be between a value of 0 and 20')
    
    def get_spread_sheet(self):
        '''
        Make a post request to the server with adequate parameters 
        then save retrieved data to an excel file
        '''    
        params = deepcopy(self._params)

        params['srchCond'] = '1'
        params['workType'] = 'EX'

        try:
            res = requests.post(self._excel_url, params, timeout=10)
            return res.content
        except requests.exceptions.RequestException as RequestException:
            self.log_message(RequestException, 'error')
            return None

    def save_spread_sheet(self, filename):
        '''
        Save response content(excel file) as given filename
        '''

        self.log_message(f'Saving spreadsheet to local machine: {filename}', 'info')

        with open(join('xls', filename), 'wb') as output_file:
            if self.get_spread_sheet() != None:
                output_file.write(self.get_spread_sheet())

    def load_spread_sheet(self, filename):
        '''
        Load an excel spreadsheet into a pandas dataframe object
        '''
        filepath = join('xls', filename)
        df = pd.read_excel(filepath, skiprows=[0,1])
        return df

    def get_lecture_list(self, df):
        '''
        Return a list of dict objects for each lecture
        '''

        lectures = []
        columns = [column for column in df.columns]

        for index, row in df.iterrows():
            lecture = {}
            for column in columns:
                lecture[column] = row[column]
            lecture['isFull'] = int(lecture['정원'].split(' ')[0]) <= int(lecture['수강신청인원'])
            lecture['users'] = []
            lectures.append(lecture)

        return lectures
    
    def save_df_to_db(self, df):
        '''
        Save data in dataframe to database
        '''
        self.log_message('Saving spreadsheet to database(INITIALIZING DATABASE)', 'info')
        
        lectures = self.get_lecture_list(df)
        for lecture in lectures:
            self.db.lectures.insert_one(lecture)

    def update_df_to_db(self, df):
        '''
        Add new lecture to the database
        '''

        self.log_message('Updating spreadsheet to database', 'info')

        lectures = self.get_lecture_list(df)

        for lecture in lectures:
            lecture_code = lecture['교과목번호']
            lecture_number = int(lecture['강좌번호'])

            lecture_cursor = self.db.lectures.find_one({
                '$and': [
                    { '교과목번호': lecture_code },
                    { '강좌번호': int(lecture_number) }
                ]
            })

            if lecture_cursor == None:
                self.db.lectures.insert_one(lecture)

           
    def get_page_student_data(self, page_num):
        '''
        Return dict of number of students for each course on the page
        '''
        
        params = deepcopy(self._params)

        params['srchCond'] = '0'
        params['pageNo'] = str(page_num)
        params['workType'] = 'S'
        
        find_data = []

        try:
            res = requests.post(self._site_url, params, timeout=10)
        except requests.exceptions.RequestException as RequestException:
            self.log_message(RequestException, 'error')
            return find_data

        soup = BeautifulSoup(res.content, 'html.parser')
        data = soup.findAll('td', { 'rowspan': True })

        for i in range(len(data[1:])):
            if i % 15 == 14:
                lecture_data = {
                    '교과목번호': data[i - 7].getText(),
                    '강좌번호': int(data[i - 6].getText()),
                    '수강신청인원': int(data[i].getText())
                }
                find_data.append(lecture_data)
        
        return find_data 


    def get_student_data(self):
        '''
        Get data for all students on all pages
        '''
        
        updated_student_data = []

        for i in range(1, self.max_page_num + 1):
            updated_data = self.get_page_student_data(i)
            for data in updated_data:
                updated_student_data.append(data)

        return updated_student_data
    
    def send_messages(self, lecture):
        users = lecture['users']
        lecture_title = lecture['교과목명']
        user_counter = 0
        
        # Send FCM messages
        for user in users:
            user_token = user
            message = messaging.Message(
                notification = messaging.Notification(
                    title= '수강신청 빈자리 알림',
                    body= f'강좌 {lecture_title}에 빈자리가 생겼습니다.'
                ),
                token = str(user_token)
            )
            try:
                response = messaging.send(message)
                user_counter += 1
            except Exception:
                continue 
        self.log_message(f'Successfully sent messages to {user_counter} users.', 'info')
    
    def update_db(self, debug_data = None):
        '''
        Update student number for each lecture in the database
        '''
        
        if self.debug == True and debug_data != None:
            updated_nums = debug_data
        elif self.debug == True and debug_data == None:
            updated_nums = self.get_student_data()
        else:
            updated_nums = self.get_student_data()

        self.log_message('updating database with scraped data', 'info')

        updated_nums_data = updated_nums
        
        for data in updated_nums_data:
            updated_num = data['수강신청인원']

            lecture = self.db.lectures.find_one({
                '$and': [
                    { '교과목번호': data['교과목번호'] },
                    { '강좌번호': int(data['강좌번호']) }
                ]
            })

            # When there is a new lecture that doesn't exist in the database
            if lecture == None:
                continue
            
            id = lecture['_id']
            max_student_num = int(lecture['정원'].split(' ')[0])
            is_full = lecture['isFull']

            query = { '_id': ObjectId(id) }

            if updated_num < max_student_num and is_full == True:
                new_values = {'$set': { '수강신청인원': updated_num, 'isFull': False }}
                self.send_messages(lecture)                    
            
            elif updated_num >= max_student_num and is_full == False:
               new_values = {'$set': { '수강신청인원': updated_num, 'isFull': True }}
            
            else:
                new_values = {'$set': { '수강신청인원': updated_num } }

            # Update database
            try:
                self.db.lectures.update_one(query, new_values)
            except ValueError:
                continue

    def run(self):
        '''
        Send a request to the server and update database
        every 'time_interval' minutes 
        '''

        counter = 0
        
        xls_filename = f'{self.year}-{self.season}.xls'
        debug_xls_filename = f'{self.year}-{self.season}-debug.xls'

        self.log_message('##################### STARTING APP #####################', 'info')

        while True:
            if counter % 7 == 0:
                self.save_spread_sheet(xls_filename)
                
                if self.debug == True:
                    df = self.load_spread_sheet(debug_xls_filename)
                else:
                    df = self.load_spread_sheet(xls_filename)

                self.update_df_to_db(df)
            
            self.log_message('Scraping...', 'info')            
            self.update_db()
            self.log_message(f'Sleeping for {self._time_interval} minutes', 'info')            
            time.sleep(self._time_interval * 60)

            counter += 1


def init_scraper(scraper_app, time_interval):
    scraper_app.set_time_interval(time_interval)
    
    seasons = ['1학기', '여름학기', '2학기', '겨울학기']
    if int(scraper_app.year) >= 2019 and scraper_app.season in seasons:
        scraper_app.save_spread_sheet(f'{scraper_app.year}-{scraper_app.season}.xls')

        df = scraper_app.load_spread_sheet(f'{scraper_app.year}-{scraper_app.season}.xls')
        scraper_app.save_df_to_db(df)
    else:
        raise ValueError(
            '''
            ERROR! Parameters for 'init_scraper' must be over 2018 and one of choices: '1학기', '여름학기', '2학기', '겨울학기'
            '''
        )