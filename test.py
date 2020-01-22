from SnuScraper import client
from SnuScraper.scraper import SnuScraper, init_scraper
from os.path import join
import json
import time

db = client.SSLT2019WINTER
app = SnuScraper('2019', '겨울학기', 'U000200002U000300002', 25, db)

for data in app.get_student_data():
    print(data)
    print(type(data))