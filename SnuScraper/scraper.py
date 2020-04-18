import requests
import json
import time
import re
import threading
import pandas as pd
import firebase_admin
from firebase_admin import messaging
from os.path import join
from copy import copy, deepcopy
from bson.objectid import ObjectId
from bs4 import BeautifulSoup
from SnuScraper import config, logger

class SnuScraper(object):

    def __init__(self, year, season, id, max_page_num, db, old_students=False, debug=False):
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
        self.old_students = old_students
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
    
    def get_appropriate_season(self):
        if self.season == '1학기':
            return 'SPRING'
        elif self.season == '여름학기':
            return 'SUMMER'
        elif self.season == '2학기':
            return 'AUTUMN'
        elif self.season == '겨울학기':
            return 'WINTER'
        else:
            raise ValueError('Season value not in values of ["1학기", "여름학기", "2학기", "겨울학기"]')

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
            if self.old_students == True:
                if re.search(r'(\s*)(.?\d+)(\s*)(\((\s*)(.?\d+)(\s*)\))(\s*)', lecture['정원']):
                    # TODO: Use regex later
                    lecture['is_full'] = int(lecture['정원'].split(' ')[-1][1:-1]) <= int(lecture['수강신청인원'])
                else:
                    lecture['is_full'] = int(lecture['정원']) <= int(lecture['수강신청인원'])
            else:
                lecture['is_full'] = int(lecture['정원'].split(' ')[0]) <= int(lecture['수강신청인원'])
            lecture['users'] = []
            lectures.append(lecture)

        return lectures
    
    def insert_lecture(self, cursor, lecture_info):
        insert_query_text = '''INSERT INTO lectures (
            year,
            season, 
            교과구분, 
            개설대학, 
            개설학과, 
            이수과정, 
            학년, 
            교과목번호, 
            강좌번호, 
            교과목명, 
            부제명, 
            학점, 
            강의, 
            실습, 
            수업교시, 
            수업형태, 
            강의실, 
            주담당교수, 
            정원, 
            수강신청인원, 
            비고, 
            강의언어, 
            개설상태, 
            is_full
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'''
        
        insert_data = (
            int(self.year), 
            self.get_appropriate_season(), 
            lecture['교과구분'],
            lecture['개설대학'],
            lecture['개설학과'],
            lecture['이수과정'],
            lecture['학년'],
            lecture['교과목번호'],
            lecture['강좌번호'],
            lecture['교과목명'],
            lecture['부제명'],
            lecture['학점'],
            lecture['강의'],
            lecture['실습'],
            lecture['수업교시'],
            lecture['수업형태'],
            lecture['강의실(동-호)(#연건, *평창)'],
            lecture['주담당교수'],
            lecture['정원'],
            lecture['수강신청인원'],
            lecture['비고'],
            lecture['강의언어'],
            lecture['개설상태'],
            lecture['is_full']
        )

        cursor.execute(insert_query_text, insert_data)

    def parse_lecture_info_to_dict(self, lecture_info):
        return {
            'id': lecture_info[0],
            'year': lecture_info[1],
            'season': lecture_info[2],
            '교과구분': lecture_info[3],
            '개설대학': lecture_info[4],
            '개설학과': lecture_info[5],
            '이수과정': lecture_info[6],
            '학년': lecture_info[7],
            '교과목번호': lecture_info[8],
            '강좌번호': lecture_info[9],
            '교과목명': lecture_info[10],
            '부제명': lecture_info[11],
            '학점': lecture_info[12],
            '강의': lecture_info[13],
            '실습': lecture_info[14],
            '수업교시': lecture_info[15],
            '수업형태': lecture_info[16],
            '강의실': lecture_info[17],
            '주담당교수': lecture_info[18],
            '정원': lecture_info[19],
            '수강신청인원': lecture_info[20],
            '비고': lecture_info[21],
            '강의언어': lecture_info[22],
            '개설상태': lecture_info[23],
            'is_full': lecture_info[24]
        }

    def save_df_to_db(self, df):
        '''
        Save data in dataframe to database
        '''
        self.log_message('Saving dataframe to database(INITIALIZING DATABASE)', 'info')
        
        cursor = self.db.cursor()
        lectures = self.get_lecture_list(df)

        for lecture in lectures:
            self.insert_lecture(cursor, lecture_info)

        try:
            self.db.commit()
        except:
            self.log_message('Can\'t commit to database. Rolling back...', 'error')

    def update_df_to_db(self, df):
        '''
        Add new lecture to the database
        '''

        self.log_message('Updating spreadsheet to database', 'info')

        cursor = self.db.cursor()
        lectures = self.get_lecture_list(df)

        for lecture in lectures:
            lecture_code = lecture['교과목번호']
            lecture_number = int(lecture['강좌번호'])

            search_query_text = 'SELECT * FROM lectures WHERE 교과목번호 = %s AND 강좌번호 = %s LIMIT 1'
            query_data = (lecture_code, lecture_number)

            cursor.execute(search_query_text, query_data)
            result = cursor.fetchall()[0]

            if result == None:
                self.insert_lecture(cursor, lecture)
                cursor.execute(insert_query_text, insert_data)

        try:
            self.db.commit()
        except:
            self.log_message('Can\'t commit to database. Rolling back...', 'error')

           
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
            res = requests.post(self._site_url, params, timeout=3)
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
                    '정원': data[i - 1].getText(),
                    '수강신청인원': int(data[i].getText())
                }
                find_data.append(lecture_data)
        
        return find_data 

    def get_page_student_data_async(self, list_to_save, page_num):
        results = self.get_page_student_data(page_num)
        for result in results:
            list_to_save.append(result)
    
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

    def get_student_data_async(self):
        threads = []
        updated_student_data = []

        for i in range(1, self.max_page_num + 1):
            # LIMIT THE NUMBER OF CONCURRENT REQUESTS TO 4
            if len(threads) >= 4:
                for thread in threads:
                    thread.join()
                threads.clear()
            
            get_data_thread = threading.Thread(target=self.get_page_student_data_async, args=(updated_student_data, i))
            get_data_thread.start()
            threads.append(get_data_thread)

            # CLEAN UP LEFTOVER THREADS
            if i == self.max_page_num:
                for thread in threads:
                    thread.join()
                threads.clear()

        return updated_student_data
    
    def send_messages(self, lecture):
        # TODO: Test this function after adding devices to the database

        if self.debug == True:
            return
        
        self.log_message('Sending messages', 'info')
        # users = lecture['users']
        
        cursor = self.db.cursor()
        
        id = lecture['id']
        lecture_title = lecture['교과목명']
        user_counter = 0

        search_query_text = '''
        SELECT devices.device_token FROM lectures 
        INNER JOIN registered 
        ON registered.lecture_id = lectures.id
        INNER JOIN users
        ON registered.user_id = users.id
        INNER JOIN devices
        ON users.id = devices.user_id
        WHERE lectures.id = %s;
        '''

        cursor.execute(search_query_text, (id))
        users = [token_data[0] for token_data in cursor.fetchall()]

        # Send FCM messages
        for user in users:
            user_token = user
            message = messaging.Message(
                notification = messaging.Notification(
                    title= '수강신청 빈자리 알림',
                    body= f'강좌 {lecture_title}에 빈자리가 생겼습니다.'
                ),
                token = str(user_token),
                android = messaging.AndroidConfig(
                    priority = 'high',
                    notification = messaging.AndroidNotification(sound='default')
                ),
                apns = messaging.APNSConfig(
                    payload = messaging.APNSPayload(aps=messaging.Aps(sound='default'))
                )
            )
            try:
                response = messaging.send(message)
                user_counter += 1
            except Exception as e:
                self.log_message(f'ERROR while sending messages: {str(e)}', 'error')
                continue 
        self.log_message(f'Successfully sent messages to {user_counter} users.', 'info')
    
    def extract_max_student_number(self, max_student_data):
        if self.old_students == True:
            if re.search(r'(\s*)(.?\d+)(\s*)(\((\s*)(.?\d+)(\s*)\))(\s*)', max_student_data):
                max_student_num = int(max_student_data.split(' ')[-1][1:-1])
            else:
                max_student_num = int(max_student_data)
        else:
            max_student_num = int(max_student_data.split(' ')[0])

        return max_student_num
    
    def update_db(self):
        '''
        Update student number for each lecture in the database
        '''

        self.log_message('updating database with scraped data', 'info')
        updated_nums = self.get_student_data_async()

        updated_nums_data = updated_nums
        messaging_threads = []
        cursor = self.db.cursor()

        for data in updated_nums_data:
            updated_max_num = data['정원']
            updated_num = data['수강신청인원']

            search_query_text = 'SELECT * FROM lectures WHERE 교과목번호 = %s AND 강좌번호 = %s LIMIT 1;'
            search_data = (data['교과목번호'], int(data['강좌번호']))

            cursor.execute(search_query_text, search_data)
            lecture = self.parse_lecture_info_to_dict(cursor.fetchall()[0])

            # When there is a new lecture that doesn't exist in the database
            if lecture == None:
                continue

            max_student_num = self.extract_max_student_number(lecture['정원'])
            updated_max_student_num = self.extract_max_student_number(updated_max_num)

            id = lecture['id']
            is_full = lecture['is_full']

            if updated_num < updated_max_student_num and is_full == True:
                self.log_message(f'1, title: {lecture["교과목명"]}, updated_num: {updated_num}, max_student_num: {updated_max_student_num}', 'info')

                update_query_text = 'UPDATE lectures SET 수강신청인원 = %s, is_full = %s, 정원 = %s WHERE id = %s;'
                update_query_data = (updated_num, False, updated_max_num, id)
                
                messaging_thread = threading.Thread(target=self.send_messages, args=(lecture,))
                messaging_threads.append(messaging_thread)
                messaging_thread.start()            
            
            elif updated_num >= updated_max_student_num and is_full == False:
                self.log_message(f'2, title: {lecture["교과목명"]}, updated_num: {updated_num}, max_student_num: {updated_max_student_num}', 'info')
                
                update_query_text = 'UPDATE lectures SET 수강신청인원 = %s, is_full = %s, 정원 = %s WHERE id = %s;'
                update_query_data = (updated_num, True, updated_max_num, id) 
            
            else:
                update_query_text = 'UPDATE lectures SET 수강신청인원 = %s, 정원 = %s WHERE id = %s;'
                update_query_data = (updated_num, updated_max_num, id)

            # Update database
            cursor.execute(update_query_text, update_query_data)

        try:
            self.db.commit()
        except:
            self.log_message('Can\'t commit to database. Rolling back...', 'error')

        for messaging_thread in messaging_threads:
            if messaging_thread:
                messaging_thread.join()

    def run(self):
        '''
        Send a request to the server and update database
        every 'time_interval' minutes 
        '''

        counter = 0
        
        xls_filename = f'{self.year}-{self.season}.xls'

        self.log_message('##################### STARTING APP #####################', 'info')

        while True:
            if counter % 7 == 0:
                self.save_spread_sheet(xls_filename)
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

def init_scraper_for_new_students(scraper_app):
    all_lectures = scraper_app.db.lectures.find({})

    for lecture in all_lectures:
        current_number = lecture['수강신청인원']
        
        # Match for lectures that have a limit on how many old students can register
        # Match for +, - signs as implemented above
        if re.search(r'(\s*)(\d+)(\s*)(\((\s*)(\d+)(\s*)\))(\s*)', lecture['정원']) and lecture['isFull'] == True:
            # TODO: Implement with regex later
            if int(lecture['정원'].split(' ')[0]) == int(lecture['정원'].split(' ')[-1][1:-1]):
                continue
            else:
                scraper_app.db.lectures.update_one(
                    { '_id': lecture['_id'] },
                    { '$set': { 'isFull': False } }
                )