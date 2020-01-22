import requests
import json
import time
import pandas as pd
import firebase_admin
from firebase_admin import messaging
from os.path import join
from copy import copy
from bson.objectid import ObjectId
from bs4 import BeautifulSoup
from SnuScraper import config

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
        self._time_interval = 7
        self.year = year
        self.id = id
        self.season = season
        self.max_page_num = max_page_num
        self.db = db
        self.admin = firebase_admin.initialize_app()
        self.debug = debug

        self.set_params()

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
        
        if 1 <= time_interval <=20:
            self._time_interval = time_interval
        else:
            raise ValueError('Parameter \'time_interval\' of function \'set_time_interval\' must be between a value of 1 and 20')
    
    def get_spread_sheet(self):
        '''
        Make a post request to the server with adequate parameters 
        then save retrieved data to an excel file
        '''    
        params = copy(self._params)

        params['srchCond'] = '1'
        params['workType'] = 'EX'

        res = requests.post(self._excel_url, params)

        return res.content

    def save_spread_sheet(self, filename):
        '''
        Save response content(excel file) as given filename
        '''

        with open(join('xls', filename), 'wb') as output_file:
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
            lectures.append(lecture)

        return lectures
    
    def save_df_to_db(self, df):
        '''
        Save data in dataframe to database
        '''
        lectures = self.get_lecture_list(df)
        for lecture in lectures:
            self.db.lectures.insert_one(lecture)
           
    def get_page_student_nums(self, page_num):
        '''
        Return list of number of students for each course on the page
        '''

        params = copy(self._params)

        params['srchCond'] = '1'
        params['pageNo'] = str(page_num)
        params['workType'] = 'S'
        
        res = requests.post(self._site_url, params)

        soup = BeautifulSoup(res.content, 'html.parser')
        data = soup.findAll('td', { 'rowspan': True })

        if self.debug == True:            
            find_data = []

            for i in range(len(data[1:])):
                if i % 15 == 14:
                    lecture_data = {
                        '교과목번호': data[i - 7].getText(),
                        '강좌번호': data[i - 6].getText(),
                        '수강신청인원': int(data[i].getText())
                    }
                    find_data.append(lecture_data)
            
            return find_data 
        else:
            find_number = []

            for i in range(len(data[1:])):
                if i % 15 == 14:
                    find_number.append(data[i].getText())

            return find_number


    def get_student_data(self):
        updated_student_nums = []

        for i in range(1, self.max_page_num + 1):
            updated_nums_for_page = self.get_page_student_nums(i)
            for num in updated_nums_for_page:
                updated_student_nums.append(int(num))

        return updated_student_nums
    
    
    def update_db(self, debug_data = None):
        '''
        Update student number for each lecture in the database
        '''
        
        if self.debug == True and debug_data != None:
            updated_nums = debug_data
        else:
            updated_nums = self.get_student_data()

        cursors = self.db.lectures.find()
        nums_id = 0

        for cursor in cursors:
            id = cursor['_id']
            max_student_num = int(cursor['정원'].split(' ')[0])
            title = cursor['교과목명']
            is_full = cursor['isFull']

            query = {'_id': ObjectId(id)}

            if updated_nums[nums_id] < max_student_num and is_full == True:
                new_values = {'$set': { '수강신청인원': updated_nums[nums_id], 'isFull': False }}
                users = cursor['users']

                # Send FCM messages
                
                for user in users:
                    user_token = user
                    message = messaging.Message(
                        notification = {
                            'title': '수강신청 빈자리 알림',
                            'body': f'강좌 {title}에 빈자리가 생겼습니다.'
                        },
                        token = str(user_token)
                    )
                    response = messaging.send(message)
                    print(f'Successfully sent message: {response}')

            elif updated_nums[num_id] >= max_student_num and is_full == False:
                new_values = {'$set': { '수강신청인원': updated_nums[nums_id], 'isFull': True }}

            else:
                new_values = {'$set': { '수강신청인원': updated_nums[nums_id] } }
                
            # Update database
            try:
                self.db.lectures.update_one(query, new_values)
            except IndexError:
                continue

            nums_id += 1


    def run(self):
        '''
        Send a request to the server and update database
        every 'time_interval' minutes 
        '''
        while True:
            print('Running...')
            self.update_db
            time.sleep(self._time_interval * 60)


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
