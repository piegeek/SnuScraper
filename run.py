from SnuScraper import client
from SnuScraper.scraper import SnuScraper, init_scraper
import json
import time


t1 = time.time()

db = client.SSLT2019WINTER

t2 = time.time()

app = SnuScraper('2019', '겨울학기', 'U000200002U000300002', 25, db)

# t3 = time.time()

# init_scraper(app)

t4 = time.time()

app.update_db()

t5 = time.time()

print(t5 - t4)

# print(f'db connection time: { t2 - t1 }, app creation overhead: { t3 - t2 }, create database: { t4 - t3 }, update database: { t5 - t4 }, overall: { t5 - t1 }')