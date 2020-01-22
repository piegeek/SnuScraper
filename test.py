from SnuScraper import client
from SnuScraper.scraper import SnuScraper, init_scraper
from os.path import join
import json
import time

db = client.SSLT2019WINTER
app = SnuScraper('2019', '겨울학기', 'U000200002U000300002', 25, db, debug=True)

page = 3

with open(join('test_output', f'page-{page}.html'), 'w', encoding='utf-8') as f:
    for data in app.get_page_student_nums(page):
        f.write(json.dumps(data, ensure_ascii=False) + '\n')
